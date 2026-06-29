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
        self.asset_count = self.ci.get(
            f'workspaces/{self.ci.workspace_id}/contents?kind=asset&limit=1'
        )['count']
        log.success(f'Get asset count: {self.asset_count}')
        # With this worker scaling, 300k assets would use 34 workers with 89 pages each
        # 1M assets would use 62 workers with 161 pages each.
        workers = int(self.asset_count**0.5 // 16 + 1)
        log.info(f'Using {workers} workers to ingest {self.asset_count} assets')
        self.chunks = [
            list(chunk)
            for chunk in chunks_sequential(range(self.asset_count // 100 + 1), workers)
        ]
        self.next(self.ingest_pages, foreach='chunks')

    @secrets(sources=['CLAMS-SonyCi-API', 'CLAMS-chowda-secret'])
    @step
    def ingest_pages(self):
        """Ingest a batch of asset pages"""
        log.info(f'Ingest pages {self.input}')
        page_results = []
        for page in self.input:
            page_results.append(self.batch_ingest_page(page))
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
        self.next(self.join)

    @step
    def join(self, inputs):
        """Join all threads."""
        self.updated = [i.updated for i in inputs]
        self.errors = [len(i.errors) for i in inputs]
        log.success(f'Joined {len(self.updated)} threads')
        self.next(self.end)

    @step
    def end(self):
        """Report results"""
        log.success(f'Successfully ingested {sum(self.updated)} assets')
        log.debug(self.updated)
        if sum(self.errors):
            log.error(f'Encountered {sum(self.errors)} errors: {self.errors}')
        else:
            log.success('No errors encountered!')

    def get_batch(self, n):
        return self.ci.get(
            f'workspaces/{self.ci.workspace_id}/contents?kind=asset&limit=100&offset={n*100}'
        )['items']

    def batch_ingest_page(self, n):
        from re import search, split

        from sqlmodel import Session, select

        from chowda.db import engine
        from chowda.models import MediaFile, SonyCiAsset
        from chowda.utils import upsert

        batch = self.get_batch(n)
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
                        log.debug('Skipping non-media asset: ', asset.id, asset.name, asset.type)
                        db.commit()
                        continue
                    # If the name doesn't end with .mp3 or .mp4, skip
                    if not search(r'\.mp[34]$', asset.name):
                        log.debug('Skipping non mp3/mp4 asset: ', asset.id, asset.name, asset.type)
                        db.commit()
                        continue
                    # If the name doesn't match the guid pattern, log a warning and skip it
                    if not search(r'^cpb[-_/]aacip[-_/].*\.mp[34]$', asset.name):
                        log.warning('Non-guid filename: ', asset.id, asset.name)
                        warnings.append(('non-guid', asset.id, asset.name))
                        db.commit()
                        continue
                    # It's a MediaFile!
                    # Replace '_' and '/' with '-' in the name, and remove '-dupe' if present
                    name = asset.name[10:-4]
                    ext = asset.name[-4:]
                    # if search(r'[_/]', name[:5]):
                    #     log.warning('replacing _ or / with - in guid portion of filename: ', asset.id, asset.name)
                    #     pos = search(r'[_/]', name[:5]).start()
                    #     name = name[:pos] + '-' + name[pos+1:]
                    name = name.replace('-dupe', '').replace('.mp4', '').replace('.mp3', '')
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
