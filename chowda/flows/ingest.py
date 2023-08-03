from metaflow import FlowSpec, secrets, step, trigger

from chowda.log import log


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

        self.chunks = [
            list(chunk)
            for chunk in chunks_sequential(range(self.asset_count // 100 + 1), 16)
        ]
        self.next(self.ingest_pages, foreach='chunks')

    @step
    def ingest_pages(self):
        """Ingest a batch of asset pages"""
        log.info(f'Ingest pages {self.input}')
        self.results = []
        for page in self.input:
            self.results.append(self.batch_ingest_page(page))
        self.results = sum(self.results)
        log.success(f'Ingested batch {self.input} with {self.results} assets')
        self.next(self.join)

    @step
    def join(self, inputs):
        """Join all threads."""
        self.results = [i.results for i in inputs]
        log.success(f'Joined {len(self.results)} threads')
        log.info(self.results)
        self.next(self.end)

    @step
    def end(self):
        """Report results"""
        log.success(f'Successfully ingested {sum(self.results)} assets')
        log.info(self.results)

    def get_batch(self, n):
        return self.ci.get(
            f'workspaces/{self.ci.workspace_id}/contents?kind=asset&limit=100&fields=id,name,type,size,thumbnails,format&offset={n*100}'
        )['items']

    def batch_ingest_page(self, n):
        from re import search, split

        from sqlmodel import Session, select

        from chowda.db import engine
        from chowda.models import MediaFile, SonyCiAsset
        from chowda.utils import upsert

        with Session(engine) as session:
            batch = self.get_batch(n)
            media = [SonyCiAsset(**asset) for asset in batch]
            results = []
            for asset in media:
                results.append(session.execute(upsert(SonyCiAsset, asset, ['id'])))
                # If it's a GUID
                if search('^cpb-aacip-', asset.name):
                    # Extract the GUID name
                    guid = split(r'_|\.|-dupe', asset.name)[0]
                    # Check for existing MediaFile
                    media_file = session.exec(
                        select(MediaFile).where(MediaFile.guid == guid)
                    ).first()
                    if not media_file:
                        # Create a new MediaFile with the new guid
                        media_file = MediaFile(guid=guid)
                    ci_asset = session.get(SonyCiAsset, asset.id)
                    # Add the asset to the existing MediaFile
                    media_file.assets.append(ci_asset)
                    session.add(media_file)

            result = sum([r.rowcount for r in results])
            session.commit()
            log.success(f'Ingested page {n} with {result} assets')
            return result


if __name__ == '__main__':
    IngestFlow()
