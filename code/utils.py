
def error(error_class: str, error_message: str, debug=False) -> dict:
	"""Returns a dictionary with error information, optionally printing it to the
	standard output."""
	message = {
		"status": "error",
		"error-class": error_class,
		"error-message": error_message }
	if debug:
		print(message)
	return message
