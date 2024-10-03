class DownloadException(Exception):
    def __init__(self, download_errors: dict[str, Exception]) -> None:
        self.download_errors = download_errors
        super().__init__(f'Error downloading MMIF files: {download_errors}')
