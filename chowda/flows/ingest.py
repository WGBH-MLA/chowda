from metaflow import FlowSpec, step, trigger, secrets

from chowda.log import log
from chowda.models import AssetType

asset_types = {AssetType('Video'), AssetType('Audio')}


@trigger(event='sync')
class IngestFlow(FlowSpec):
    """Ingest all assets from SonyCi."""

    @secrets(sources=['CLAMS-SonyCi-API'])
    @step
    def start(self):
        """Get total asset count and start batch ingest."""
        from sonyci import SonyCi

        from chowda.utils import chunks_sequential

        self.ci = SonyCi(**SonyCi.from_env())
        self.ci.login()
        # Asset ingest
        self.asset_count = self.get_asset_count()
        log.success(f'Get asset count: {self.asset_count}')
        # With this worker scaling, 300k assets would use 34 workers with 89 pages each
        # 1M assets would use 62 workers with 161 pages each.
        workers = int(self.asset_count**0.5 // 20 + 1)
        log.info(f'Using {workers} workers to ingest {self.asset_count} assets')
        self.chunks = [
            list(chunk)
            for chunk in chunks_sequential(range(self.asset_count // 100 + 1), workers)
        ]
        self.next(self.ingest_assets, foreach='chunks')

    @secrets(sources=['CLAMS-SonyCi-API', 'CLAMS-chowda-secret'])
    @step
    def ingest_assets(self):
        """Ingest a batch of asset pages"""
        log.info(f'Ingest pages {self.input}')
        page_results = []
        for page in self.input:
            page_results.append(self.batch_ingest_assets_page(page))
        self.updated: int = sum([r.get('updated', 0) for r in page_results])
        self.errors: list = [r.get('errors', []) for r in page_results]
        self.errors = [
            1 for sublist in self.errors for e in sublist
        ]  # Flatten list of lists
        if sum(self.errors) > 0:
            log.error(
                f'Encountered {len(self.errors)} errors ingesting batch {self.input}'
            )
        log.success(f'Ingested batch {self.input} with {self.updated} assets')
        self.next(self.join_assets)

    @step
    def join_assets(self, inputs):
        """Join all threads."""
        self.updated = [i.updated for i in inputs]
        self.errors = [len(i.errors) for i in inputs]
        log.info(f'Joined {len(self.updated)} threads')
        log.success(f'Successfully ingested {sum(self.updated)} assets')
        if sum(self.errors):
            log.error(f'Encountered {sum(self.errors)} errors: {self.errors}')
        else:
            log.success('No errors encountered!')
        self.next(self.trashbin_start)

    @secrets(sources=['CLAMS-SonyCi-API'])
    @step
    def trashbin_start(self):
        from chowda.utils import chunks_sequential
        from sonyci import SonyCi

        self.ci = SonyCi(**SonyCi.from_env())
        self.ci.login()

        # Trashbin ingest
        trashbin_count = self.get_asset_count('trashbin')
        log.success(f'Get trashbin count: {trashbin_count}')
        workers = int(trashbin_count**0.5 // 16 + 1)
        log.info(f'Using {workers} workers to ingest {trashbin_count} trashbin items')
        self.trashbin_chunks = [
            list(chunk)
            for chunk in chunks_sequential(range(trashbin_count // 100 + 1), workers)
        ]
        self.next(self.ingest_trashbin_batch, foreach='trashbin_chunks')

    @secrets(sources=['CLAMS-SonyCi-API', 'CLAMS-chowda-secret'])
    @step
    def ingest_trashbin_batch(self):
        """Ingest a batch of trashbin items"""
        from chowda.db import engine
        from chowda.models import SonyCiTrashbin, SonyCiAsset
        from chowda.utils import upsert
        from sqlmodel import Session

        self.ingested = 0
        self.trashed = 0
        self.errors = []
        for page in self.input:
            log.info(f'Ingesting trashbin page {page}')

            trashbin = self.get_page(page, path='trashbin')
            log.info(f'Ingesting {len(trashbin)} trashbin items')
            with Session(engine) as db:
                for item in trashbin:
                    try:
                        db.exec(upsert(SonyCiTrashbin, SonyCiTrashbin(**item), ['id']))
                        self.ingested += 1
                        # If the item is an existing SonyCiAsset, remove it from the SonyCiAsset table
                        if db.get(SonyCiAsset, item['id']):
                            db.delete(db.get(SonyCiAsset, item['id']))
                            self.trashed += 1
                        db.commit()
                    except Exception as e:
                        log.error(f'Error ingesting trashbin item {item["id"]}: {e}')
                        self.errors.append((item['id'], e))
        log.success(
            f'Ingested {self.ingested} trashbin items, trashed {self.trashed} assets'
        )
        self.next(self.join_trashbin)

    @step
    def join_trashbin(self, inputs):
        """Join all trashbin threads."""
        self.ingested = [i.ingested for i in inputs]
        self.trashed = [i.trashed for i in inputs]
        self.errors = [len(i.errors) for i in inputs]
        if sum(self.errors):
            log.error(f'Encountered {sum(self.errors)} errors')
            log.debug(self.errors)
        else:
            log.success('No errors encountered!')
        self.next(self.end)

    @step
    def end(self):
        """Report results"""
        log.debug(f'ingested: {self.ingested}')
        if sum(self.ingested):
            log.success(f'Successfully ingested {sum(self.ingested)} trashbin items')
        log.debug(f'trashed: {self.trashed}')
        if sum(self.trashed):
            log.success(f'Successfully trashed {sum(self.trashed)} assets')
        log.debug(f'errors: {self.errors}')
        if sum(self.errors):
            log.warning(f'Encountered {sum(self.errors)} errors')
        else:
            log.success('No errors encountered!')

    def get_asset_count(self, path='contents') -> int:
        return self.ci.get(
            f'workspaces/{self.ci.workspace_id}/{path}?kind=asset&limit=1'
        )['count']

    def get_page(self, page, path='contents', limit=100):
        return self.ci.get(
            f'workspaces/{self.ci.workspace_id}/{path}?kind=asset&limit={limit}&offset={page*limit}'
        )['items']

    def batch_ingest_assets_page(self, n):
        from re import search, split

        from sqlmodel import Session, select

        from chowda.db import engine
        from chowda.models import MediaFile, SonyCiAsset
        from chowda.utils import upsert

        batch = self.get_page(n)
        media = [SonyCiAsset(**asset) for asset in batch]
        results: list = []
        errors: list = []
        warnings: list = []

        with Session(engine) as db:
            for asset in media:
                try:
                    results.append(db.exec(upsert(SonyCiAsset, asset, ['id'])))
                    # If the asset type is not Video or Audio, skip it
                    if AssetType(asset.type) not in asset_types:
                        log.debug(
                            'Skipping non-media asset: ',
                            asset.id,
                            asset.name,
                            asset.type,
                        )
                        db.commit()
                        continue
                    # If the name doesn't end with .mp3 or .mp4, skip
                    if not search(r'\.mp[34]$', asset.name):
                        log.debug(
                            'Skipping non mp3/mp4 asset: ',
                            asset.id,
                            asset.name,
                            asset.type,
                        )
                        db.commit()
                        continue
                    # SonyCi filenames sometimes carry a leading BOM (U+FEFF), which
                    # breaks the anchored guid match and the fixed-index slice below.
                    filename = asset.name.replace('\ufeff', '').strip()
                    # If the name doesn't match the guid pattern, log a warning and skip it
                    if not search(r'^cpb[-_/]aacip[-_/].*\.mp[34]$', filename):
                        log.warning('Non-guid filename: ', asset.id, asset.name)
                        warnings.append(('non-guid', asset.id, asset.name))
                        db.commit()
                        continue
                    # It's a MediaFile!
                    # Replace '_' and '/' with '-' in the name, and remove '-dupe' if present
                    name = filename[10:-4]
                    # ext = filename[-4:]
                    # if search(r'[_/]', name[:5]):
                    #     log.warning('replacing _ or / with - in guid portion of filename: ', asset.id, asset.name)
                    #     pos = search(r'[_/]', name[:5]).start()
                    #     name = name[:pos] + '-' + name[pos+1:]
                    name = split(r"_|\.", name)[0]
                    # Should be just a the ID now
                    guid = f'cpb-aacip-{name}'
                    # Check for existing MediaFile
                    media_file = db.exec(
                        select(MediaFile).where(MediaFile.guid == guid)
                    ).first()
                    if not media_file:
                        # Create a new MediaFile with the new guid
                        media_file = MediaFile(guid=guid)
                    # Get the SonyCiAsset we just saved to the db
                    ci_asset = db.get(SonyCiAsset, asset.id)
                    # Add the asset to the existing MediaFile
                    media_file.assets.append(ci_asset)
                    db.add(media_file)
                    db.commit()
                except Exception as e:
                    log.error(f'Error ingesting asset {asset.id}: {e}')
                    errors.append((asset, e))
            updated: int = sum([r.rowcount for r in results])
            if errors:
                log.error(f'{len(errors)} errors ingesting page {n}: {errors}')
            if warnings:
                log.warning(f'{len(warnings)} warnings ingesting page {n}: {warnings}')

        log.success(f'Ingested page {n} with {updated} assets')
        return {'updated': updated, 'errors': errors}


if __name__ == '__main__':
    IngestFlow()
