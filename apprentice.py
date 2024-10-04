import csv


class Apprentice:
    OFFSET_START = 41

    NAME = 1
    ON_OFF_TRACK = 2
    SUPPORT_FACTORS = 3
    INTERVENTION = 4
    ATTENDANCE_INFO = 5
    OTJ_PERCENTAGE = 6
    # OTJ_HOURS = 23
    FS = 7

    # FS_ENGLISH = 7
    GATEWAY_BOOKED = 8
    COHORT = 9
    CLIENT = 10
    STATUS = 11

    MAPPINGS = {
        "Name": NAME,
        "On/Off Track": ON_OFF_TRACK,
        "Attendance info": ATTENDANCE_INFO,
        # "Last attendance": OTJ_PERCENTAGE,
        "OTJ %": OTJ_PERCENTAGE,
        # "OTJ hours": OTJ_HOURS,
        # "English FS": FS_ENGLISH,
        # "Maths FS": FS_MATHS,
        "Gateway booked?": GATEWAY_BOOKED,
        "Cohort": COHORT,
        "Client": CLIENT,
        "Status": STATUS,
    }

    def __init__(self):
        self.uuid = None
        self.profile_link = None
        self.name = None
        self.role = None
        self.programme = None
        self.on_off_track = None
        self.last_coaching_attendance = None
        self.last_delivery_attendance = None
        self.otj_percentage = None
        self.otj_hours = None
        self.fs_english = None
        self.fs_maths = None
        self.gateway_booked = False
        self.gateway_date = None
        self.cohort = None
        self.client = None
        self.status = None
        self.uln = None
        self.manager = None
        self.manager_email = None
        self.earliest_gateway = None
        self.expected_gateway = None
        self.timely_gateway = None
        self.epa = None
        self.delivery_attended = None
        self.delivery_missed = None
        self.days_on_programme = None

        self.notes = []
        self.projects = []

    def __str__(self):
        out = ""
        for var in vars(self):
            val = getattr(self, var)
            if val is not None:
                out += f"{var}: {str(val)} - "
        return out

    def __repr__(self):
        return self.name


class ApprenticeNote:
    AUTHOR = 2
    DATE = 3
    TEXT = 5
    MAPPINGS = {
        "Author": AUTHOR,
        "Date": DATE,
        "Text": TEXT,
    }

    def __init__(self):
        self.uuid = None
        self.author = None
        self.date = None
        self.text = None
        self.statuses = []
        self.updates = []

    def to_list(self):
        return [
            self.uuid,
            self.author,
            self.date,
            self.text,
            self.statuses,
            self.updates,
        ]

    def __str__(self):
        return str(
            [self.uuid, self.author, self.date, self.text, self.statuses, self.updates]
        )

    def __repr__(self):
        return [
            self.uuid,
            self.author,
            self.date,
            self.text,
            self.statuses,
            self.updates,
        ]


class ApprenticeProject:
    def __init__(self):
        self.name = None
        self.status = None
        self.date = None
        self.link = None

    def __str__(self):
        return str(self.name)
