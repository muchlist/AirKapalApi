class ErrorMessage():
    message = ""
    error_code = 0

    def __init__(self, message: str, error_code: int):
        message = message
        error_code = error_code
    
    def output(self):
        return {"message": message}
