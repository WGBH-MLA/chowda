from metaflow import FlowSpec, step

from chowda.log import log


class IngestFlow(FlowSpec):
    """Ingest all assets from SonyCi."""

    @step
    def start(self):
        """Get total asset count and start batch ingest."""
        from sonyci import SonyCi

        self.ci = SonyCi(**SonyCi.from_env())
        self.asset_count = self.ci.get(
            f'workspaces/{self.ci.workspace_id}/contents?kind=asset&limit=1'
        )['count']
        log.success(f'Get asset count: {self.asset_count}')

        self.pages = range(self.asset_count // 100 + 1, 100)
        self.next(self.ingest_page, foreach='pages')

    @step
    def ingest_page(self):
        """Ingest a page of assets."""
        print(f'Ingest page {self.input}')
        self.batch_ingest_session(self.input)
        # TODO: return total success/failuresexit
        log.success(f'Ingested page {self.input}')
        self.next(self.join)

    @step
    def join(self, inputs):
        """Join all threads."""
        print('Join')
        self.results = [i.result for i in inputs]
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

    def batch_ingest_session(self, n):
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
            self.result = sum([r.rowcount for r in results])
            session.commit()


if __name__ == '__main__':
    IngestFlow()
