import config


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

def get_valid_pages(total_hits: int, current_page: int) -> dict:
    """Returns a mix of self, first, last, next, and previous
    pages - depending on current_page and total_hits values"""
    pages = {}
    pages.update({"self": current_page})
    total_pages = total_hits // config.MAX_RESULTS + 1
    # if there are more pages than allowed maximum, set total_pages to MAX_PAGES
	# this may want to be set as part of elastic response (then this wouldnt be required)?
    if total_pages > config.MAX_PAGES:
        total_pages = config.MAX_PAGES
    # return mix of pages
    if current_page > total_pages:
        return pages
    if current_page != 1:
        pages.update({"first": 1})
        pages.update({"previous": current_page - 1})
    if current_page != total_pages:
        pages.update({"last": total_pages})
        pages.update({"next": current_page + 1})
    return pages
