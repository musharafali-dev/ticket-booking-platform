"""Domain-specific booking exceptions, kept separate from HTTP concerns."""


class BookingError(Exception):
    """Base class for booking domain errors."""


class SeatsUnavailableError(BookingError):
    """Raised when one or more requested seats could not be locked."""

    def __init__(self, unavailable_seat_ids: list[int]):
        self.unavailable_seat_ids = unavailable_seat_ids
        super().__init__(f"Seats unavailable: {unavailable_seat_ids}")


class BookingNotFoundError(BookingError):
    pass


class BookingExpiredError(BookingError):
    pass


class InvalidBookingStateError(BookingError):
    pass
