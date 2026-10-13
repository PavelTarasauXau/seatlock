class AppError(Exception):
    
    status_code = 500

    def __init__(self, detail: str):
        super().__init__(detail)
        self.detail = detail

class NotFoundError(AppError):

    status_code = 404

class ConflictError(AppError):

    status_code = 409

class BadRequestError(AppError):

    status_code = 400