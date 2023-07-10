from metaflow import FlowSpec, secrets, step

from chowda.log import log


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
        from sqlmodel import Session

        from chowda.db import engine
        from chowda.models import SonyCiAsset
        from chowda.utils import upsert

        with Session(engine) as session:
            batch = self.get_batch(n)
            media = [SonyCiAsset(**asset) for asset in batch]
            results = []
            for m in media:
                results.append(session.execute(upsert(SonyCiAsset, m, ['id'])))
            result = sum([r.rowcount for r in results])
            session.commit()
            log.success(f'Ingested page {n} with {result} assets')
            return result


if __name__ == '__main__':
    IngestFlow()
