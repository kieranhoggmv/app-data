import csv
from datetime import datetime as dt
from datetime import timedelta
from dotenv import load_dotenv
import os
import re
from selenium.webdriver.common.by import By
from selenium.common import exceptions
import sqlite3

from apprentice import Apprentice, ApprenticeNote, ApprenticeProject
from browser import Browser
from cohort import Cohort

load_dotenv()


class Scraper:
    CW_URL = os.getenv("CW_URL")
    PROFILE_URL = os.getenv("PROFILE_URL")
    PROJECTS_URL = os.getenv("PROJECTS_URL")

    def __init__(self):
        self.browser = None
        self.cohort = Cohort()
        self.projects = []
        self.notes = []
        self.last_updated = None
        self.con = sqlite3.connect("data.db")
        self.cur = self.con.cursor()

    def initial_update(self):
        self.browser = Browser().get_browser()
        print("Last updated: ", end="")
        try:
            with open(".updated", "r") as f:
                ts = f.read()
                self.last_updated = dt.fromtimestamp(int(ts))
                print(self.last_updated)
        except FileNotFoundError:
            print("Never")
        with open(".updated", "w") as f:
            f.write(str(int(dt.now().timestamp())))

        self.cohort.add_apprentices(self.get_apprentices())
        self.save_apprentices_to_db()

    def get_apprentices(self, full_export=False, max=None, offset=0):
        if not self.last_updated:
            self.initial_update()
        self.browser.driver.get(self.CW_URL)
        page_source = self.browser.wait_for_page_item(By.TAG_NAME, "tbody", 5)
        rows = page_source.find_all("tr")
        apprentices = []
        notes = []

        for i, row in enumerate(rows):
            while offset > 0:
                next()
                offset -= 1
            cells = row.find_all("td")
            uuid = (
                row.find_all("a")[0]["href"].split("/")[-1].replace("?back_query=", "")
            )
            this_apprentice = Apprentice()
            try:
                this_apprentice.name = (
                    cells[Apprentice.NAME]
                    .find_all("span")[-1]
                    .text.strip()
                    .replace("\n", "")
                )
                this_apprentice.on_off_track = (
                    cells[Apprentice.ON_OFF_TRACK].text.strip().replace("\n", "")
                )
                attendance_info = (
                    cells[Apprentice.ATTENDANCE_INFO].text.strip().replace("\n", "")
                )
                coaching = re.search(
                    r"Coaching • (\d+ [a-zA-Z]{3} \d{4}|No attendance recorded)",
                    attendance_info,
                )
                delivery = re.search(
                    r"Delivery • (\d+ [a-zA-Z]{3} \d{4}|No attendance recorded)",
                    attendance_info,
                )
                if coaching:
                    this_apprentice.last_coaching_attendance = coaching.group(1)
                if delivery:
                    this_apprentice.last_delivery_attendance = delivery.group(1)
                gateway_booked = (
                    True
                    if "Yes" in cells[Apprentice.GATEWAY_BOOKED].text.strip()
                    else False
                )
                gateway_details = (
                    cells[Apprentice.GATEWAY_BOOKED].text.strip().split("\n")
                )
                if len(gateway_details) > 1:
                    this_apprentice.gateway_date = dt.strptime(
                        gateway_details[0], "%d %b %Y"
                    ).date()
                this_apprentice.gateway_booked = gateway_booked
                otj_info = cells[Apprentice.OTJ_PERCENTAGE].text.strip().split("\n")
                this_apprentice.otj_percentage = otj_info[0][:-1]
                this_apprentice.otj_hours = otj_info[-1]
                fs_info = cells[Apprentice.FS].text.strip().split("\n")
                this_apprentice.fs_english = fs_info[11]
                this_apprentice.fs_maths = fs_info[0]
                # this_apprentice.fs_maths = cells[Apprentice.FS_MATHS + offset].text.strip().split("\n")
                this_apprentice.cohort = (
                    cells[Apprentice.COHORT].text.strip().replace("\n", "")
                )
                this_apprentice.client = (
                    cells[Apprentice.CLIENT].text.strip().replace("\n", "")
                )
                this_apprentice.status = (
                    cells[Apprentice.STATUS].text.strip().replace("\n", "")
                )
                this_apprentice.profile_link = f"{self.PROFILE_URL}{uuid}/"
                this_apprentice.uuid = uuid
                if full_export:
                    # notes.extend(this_apprentice.notes)
                    profile_page = self.browser.get_url_source(
                        this_apprentice.profile_link
                    )
                    self.browser
                    this_apprentice.notes = self.get_apprentice_updates(
                        uuid, profile_page
                    )
                    self.notes.extend(this_apprentice.notes)
                    this_apprentice.uln = profile_page.find(
                        "span", {"id": "qd-uln-text"}
                    ).text.strip()
                    this_apprentice.manager = (
                        profile_page.find("h2", string="Manager")
                        .find_next_sibling("div")
                        .text.strip()
                    )
                    try:
                        this_apprentice.earliest_gateway = (
                            profile_page.find("span", string="Earliest gateway date")
                            .find_next("span")
                            .text.strip()
                        )
                    except AttributeError:
                        pass
                    this_apprentice.expected_gateway = (
                        profile_page.find("span", string="Expected gateway date")
                        .find_next("span")
                        .text.strip()
                    )
                    this_apprentice.timely_gateway = (
                        profile_page.find("span", string="Timely gateway date")
                        .find_next("span")
                        .text.strip()
                    )
                    this_apprentice.epa = (
                        profile_page.find("span", string="End point assessment")
                        .find_next("span")
                        .text.strip()
                    )
                    this_apprentice.days_on_programme = (
                        profile_page.find("h2", string="Days on programme")
                        .find_next_sibling("div")
                        .text.strip()
                    )
                apprentices.append(this_apprentice)
            except IndexError:
                continue
            if i + 1 == max:
                break
            else:
                i += 1

        return apprentices

    def get_apprentice_updates(self, uuid, profile_page):
        notes = profile_page.select("#coach_world_history")[0].find_all(
            "div", {"class": "rounded"}
        )
        parsed_notes = []
        for note in notes:
            new_note = ApprenticeNote()
            new_note.uuid = uuid
            statuses = note.find_all("div", {"role": "status"})
            updates = note.find_all("div", {"class": "font-medium"})
            note_spans = note.find_all("span")

            for status in statuses:
                new_note.statuses.append(status.text.strip().replace("\n", " "))
            for update in updates:
                new_note.updates.append(update.text.strip().replace("\n", " "))
            try:
                new_note.author = note_spans[ApprenticeNote.AUTHOR].text.strip()
                note_date = note_spans[ApprenticeNote.DATE].text.strip()
                if note_date == "Just now":
                    new_note.date = dt.now().date()
                else:
                    try:
                        new_note.date = dt.strptime(note_date, "%d %b %Y")
                    except ValueError:
                        new_note.date = "Unknown"
                new_note.text = note_spans[ApprenticeNote.TEXT].text.strip()

            except IndexError:
                pass
            if new_note.text:
                parsed_notes.append(new_note)
        return parsed_notes

    def get_projects(self):
        if not self.last_updated:
            self.initial_update()

        ### Pending projects
        self.browser.driver.get(self.PROJECTS_URL + "pending")
        self.browser.wait_for_page_item(
            By.CLASS_NAME,
            "PendingProjectSubmission-module__projectsCoachSubmissionsWrapper___GCEAS",
            30,
        )
        try:
            self.browser.wait_for_page_item(
                By.XPATH,
                "//div[class='PendingProjectSubmissions-module__loadMoreButton___FuYtl']",
                2,
            )
        except:
            pass
        buttons = self.browser.driver.find_elements(
            By.CLASS_NAME, "PendingProjectSubmissions-module__loadMoreButton___FuYtl"
        )
        retries = 2
        while buttons and retries > 0:
            for button in buttons:
                try:
                    self.browser.wait_for_page_item(By.TAG_NAME, "button")
                    button.find_element(By.TAG_NAME, "button").click()
                    self.browser.wait_for_page_item(
                        By.CLASS_NAME,
                        "PendingProjectSubmissions-module__loadMoreButton___FuYtl",
                        2,
                    )
                    buttons = self.browser.driver.find_elements(
                        By.CLASS_NAME,
                        "PendingProjectSubmissions-module__loadMoreButton___FuYtl",
                    )
                except Exception as e:
                    retries -= 1
                    pass

        projects = self.browser.driver.find_element(
            By.XPATH, "//main//div[not(@id) and not(@class)]"
        )
        self.browser.wait_for_page_item(
            By.CLASS_NAME, "PendingProjectList-module__projectEntry___WVoAt", 2
        )
        NAME = 0
        STATUS = 3
        DATE = 6
        current_project = None
        for project in projects.find_elements(By.TAG_NAME, "div"):
            try:
                current_project = project.find_element(By.TAG_NAME, "h3").text
            except:
                pass

            for item in project.find_elements(
                By.CLASS_NAME,
                "PendingProjectSubmission-module__projectsCoachSubmissionsWrapper___GCEAS",
            ):
                divs = item.find_elements(By.TAG_NAME, "div")
                self.projects.append(
                    [
                        current_project,
                        divs[NAME].text,
                        divs[STATUS].text,
                        divs[DATE].text,
                    ]
                )

        ### Completed projects
        self.browser.driver.get(self.PROJECTS_URL + "completed")
        self.browser.driver.refresh()

        self.browser.wait_for_page_item(
            By.CLASS_NAME, "CompletedProjectList-module__projectsCoachList___Nk1CV", 2
        )
        for _ in range(10):
            lis = self.browser.driver.find_elements(By.TAG_NAME, "button")
            self.browser.driver.execute_script(
                "arguments[0].scrollIntoView();", lis[-1]
            )
            try:
                self.browser.wait_for_page_item(
                    By.CLASS_NAME,
                    "CompletedProjectList-module__projectsCoachList___Nk1CV",
                    0.1,
                )
            except:
                pass
        self.browser.driver.find_elements(
            By.CLASS_NAME,
            "CompletedProjectSubmissions-module__projectsCoachSubmissionsWrapper___G0Cym",
        )
        projects = self.browser.driver.find_elements(
            By.CLASS_NAME,
            "CompletedProjectSubmissions-module__projectsCoachSubmissionsWrapper___G0Cym",
        )

        # Get the projects first, then parse them separately so lower risk of page getting stale
        for p in projects:
            divs = p.find_elements(By.TAG_NAME, "div")
            try:
                name = divs[0].text
                status = divs[6].text
                date = divs[8].text
                link = divs[10].text
                self.projects.append([project, name, status, date])
            except exceptions.StaleElementReferenceException:
                divs = p.find_elements(By.TAG_NAME, "div")
                name = divs[0].text
                project = divs[3].text
                status = divs[6].text
                date = divs[7].text
                link = divs[10].text
                self.projects.append([project, name, status, date])

            # TODO: finish this
            # div.find_element(By.TAG_NAME, "button").click()
            #     div.find_element(By.TAG_NAME, "button").click()
            #     WebDriverWait(self.driver, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".menuitem > button")))
            #     div.find_element(By.CSS_SELECTOR, ".menuitem > button").click()
        for project in self.projects:
            if project:
                new_project = ApprenticeProject()
                new_project.name = project[0]
                new_project.status = project[2]
                date = project[3]
                m = re.search(r"(\d+|a)", date)
                if m:
                    number = m.group(1)
                    if number == "a":
                        number = 1
                    else:
                        number = int(number)
                    if "day" in project[3]:
                        date = dt.now() - timedelta(days=number)
                    elif "month":
                        date = dt.now() - timedelta(days=number * 30)
                new_project.date = date

                apprentice_full_name = project[1]
                if apprentice_full_name in self.cohort:
                    apprentice = self.cohort.get_apprentice(apprentice_full_name)
                    apprentice.projects.append(new_project)
        return self.projects

    def save_apprentices_to_db(self):
        self.cur.execute(
            """
            CREATE TABLE IF NOT EXISTS 
                    apprentices(
                        uuid TEXT PRIMARY KEY, 
                        total_apprentices INT, 
                        on_bil INT, 
                        on_track INT, 
                        gateway_booked INT,
                        profile_link TEXT,
                        name TEXT,
                        role TEXT,
                        programme TEXT,
                        on_off_track TEXT,
                        last_coaching_attendance TEXT,
                        last_delivery_attendance TEXT,
                        otj_percentage INTEGER,
                        otj_hours TEXT,
                        fs_english TEXT,
                        fs_maths TEXT,
                        gateway_date INTEGER,
                        cohort TEXT,
                        client TEXT,
                        status TEXT,
                        uln TEXT,
                        manager TEXT,
                        manager_email TEXT,
                        earliest_gateway INTEGER,
                        expected_gateway INTEGER,
                        timely_gateway INTEGER,
                        epa INTEGER,
                        delivery_attended INTEGER,
                        delivery_missed INTEGER,
                        days_on_programme INTEGER
                    )
        """
        )
        for apprentice in self.cohort.apprentices:
            self.cur.execute(
                "SELECT uuid FROM apprentices WHERE uuid = ?", (apprentice.uuid,)
            )
            if self.cur.fetchone():
                self.cur.execute(
                    """
                UPDATE apprentices 
                    SET 
                        profile_link = ?,
                        name = ?,
                        role = ?,
                        programme = ?,
                        on_off_track = ?,
                        last_coaching_attendance = ?,
                        last_delivery_attendance = ?,
                        otj_percentage = ?,
                        otj_hours = ?,
                        fs_english = ?,
                        fs_maths = ?,
                        gateway_booked = ?,
                        gateway_date = ?,
                        cohort = ?,
                        client = ?,
                        status = ?,
                        uln = ?,
                        manager = ?,
                        manager_email = ?,
                        earliest_gateway = ?,
                        expected_gateway = ?,
                        timely_gateway = ?,
                        epa = ?,
                        delivery_attended = ?,
                        delivery_missed = ?,
                        days_on_programme = ?
                WHERE uuid = ?
                """,
                    (
                        apprentice.profile_link,
                        apprentice.name,
                        apprentice.role,
                        apprentice.programme,
                        apprentice.on_off_track,
                        apprentice.last_coaching_attendance,
                        apprentice.last_delivery_attendance,
                        apprentice.otj_percentage,
                        apprentice.otj_hours,
                        apprentice.fs_english,
                        apprentice.fs_maths,
                        1 if apprentice.gateway_booked else 0,
                        apprentice.gateway_date,
                        apprentice.cohort,
                        apprentice.client,
                        apprentice.status,
                        apprentice.uln,
                        apprentice.manager,
                        apprentice.manager_email,
                        apprentice.earliest_gateway,
                        apprentice.expected_gateway,
                        apprentice.timely_gateway,
                        apprentice.epa,
                        apprentice.delivery_attended,
                        apprentice.delivery_missed,
                        apprentice.days_on_programme,
                        apprentice.uuid,
                    ),
                )
                self.con.commit()
            else:
                self.cur.execute(
                    """
                    INSERT INTO apprentices(
                        profile_link,
                        name,
                        role,
                        programme,
                        on_off_track,
                        last_coaching_attendance,
                        last_delivery_attendance,
                        otj_percentage,
                        otj_hours,
                        fs_english,
                        fs_maths,
                        gateway_booked,
                        gateway_date,
                        cohort,
                        client,
                        status,
                        uln,
                        manager,
                        manager_email,
                        earliest_gateway,
                        expected_gateway,
                        timely_gateway,
                        epa,
                        delivery_attended,
                        delivery_missed,
                        days_on_programme,
                        uuid
                        )
                    VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) 
                    """,
                    (
                        apprentice.profile_link,
                        apprentice.name,
                        apprentice.role,
                        apprentice.programme,
                        apprentice.on_off_track,
                        apprentice.last_coaching_attendance,
                        apprentice.last_delivery_attendance,
                        apprentice.otj_percentage,
                        apprentice.otj_hours,
                        apprentice.fs_english,
                        apprentice.fs_maths,
                        apprentice.gateway_booked,
                        apprentice.gateway_date,
                        apprentice.cohort,
                        apprentice.client,
                        apprentice.status,
                        apprentice.uln,
                        apprentice.manager,
                        apprentice.manager_email,
                        apprentice.earliest_gateway,
                        apprentice.expected_gateway,
                        apprentice.timely_gateway,
                        apprentice.epa,
                        apprentice.delivery_attended,
                        apprentice.delivery_missed,
                        apprentice.days_on_programme,
                        apprentice.uuid,
                    ),
                )
                self.con.commit()

    def save_projects_to_db(self):
        # TODO: work out if a project is a resubmission
        project_ids = {}
        # FIXME: some WebElements end up in here, probably shouldn't
        unique_projects = set(
            [project[0] for project in self.projects if type(project[0]) == str]
        )
        self.cur.execute(
            """
            CREATE TABLE IF NOT EXISTS 
                    projects(
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT
                    )
        """
        )
        # cur.execute("DROP TABLE apprentice_projects")
        self.cur.execute(
            """
            CREATE TABLE IF NOT EXISTS 
                    apprentice_projects(
                        project_id INTEGER,
                        apprentice_uuid TEXT,
                        status TEXT,
                        date TEXT,
                        url TEXT,
                        UNIQUE(project_id, apprentice_uuid)
                    )
        """
        )
        for project in unique_projects:
            self.cur.execute("SELECT id FROM projects WHERE name = ?", (project,))
            r = self.cur.fetchone()
            if not r:
                self.cur.execute(
                    """
                INSERT INTO projects(name) 
                VALUES(?)
                """,
                    (project,),
                )
                self.con.commit()
                project_ids[project] = self.cur.lastrowid
            else:
                project_ids[project] = r[0]

        for apprentice in self.cohort.apprentices:
            for project in apprentice.projects:
                id = project_ids.get(str(project.name))
                if id:
                    self.cur.execute(
                        """
                    INSERT INTO apprentice_projects(project_id, apprentice_uuid, status, date, url)
                    VALUES(?, ?, ?, ?, ?) 
                    ON CONFLICT(project_id, apprentice_uuid) DO 
                        UPDATE SET
                            project_id=excluded.project_id,
                            apprentice_uuid=excluded.apprentice_uuid,
                            status=excluded.status,
                            date=excluded.date,
                            url=excluded.url
                    """,
                        (
                            id,
                            apprentice.uuid,
                            project.status,
                            project.date,
                            project.link,
                        ),
                    )
                    self.con.commit()

    def save_notes_to_db(self):
        self.cur.execute(
            """
           CREATE TABLE IF NOT EXISTS 
                apprentice_notes(
                    apprentice_uuid TEXT,
                    author TEXT,
                    date DATE,
                    text TEXT,
                    statuses TEXT,
                    updates TEXT,
                    UNIQUE(apprentice_uuid, author, date, text)
                )
        """
        )
        for note in self.notes:
            try:
                self.cur.execute(
                    """
                    INSERT INTO apprentice_notes(apprentice_uuid, author, date, text, statuses, updates)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        note.uuid,
                        note.author,
                        note.date,
                        note.text,
                        ", ".join(note.statuses),
                        ", ".join(note.updates),
                    ),
                )
                self.con.commit()
            except sqlite3.IntegrityError:
                pass

    def create_stats(self):
        total_apprentices = len(self.cohort.apprentices)
        gateway_booked = sum(
            1 for a in self.cohort.apprentices if a.gateway_booked == "Yes"
        )
        on_bil = sum(1 for a in self.cohort.apprentices if a.status != "On programme")
        on_track = sum(
            1 for a in self.cohort.apprentices if a.on_off_track == "On track"
        )
        fs_maths = sum(
            1 for a in self.cohort.apprentices if a.fs_maths == "Exempt with evidence"
        )
        fs_english = sum(
            1 for a in self.cohort.apprentices if a.fs_english == "Exempt with evidence"
        )

        # cur.execute("DROP TABLE stats")
        self.cur.execute(
            "CREATE TABLE IF NOT EXISTS stats(date DATE PRIMARY KEY, total_apprentices INT, on_bil INT, on_track INT, fs_maths INT, fs_english INT, gateway_booked INT)"
        )
        self.cur.execute(
            """
            INSERT INTO stats VALUES(?, ?, ?, ?, ?, ?, ?) 
            ON CONFLICT(date) DO 
                UPDATE SET 
                    total_apprentices=excluded.total_apprentices,
                    on_bil=excluded.on_bil,
                    on_track=excluded.on_track,
                    fs_maths=excluded.fs_maths,
                    fs_english=excluded.fs_english,
                    gateway_booked=excluded.gateway_booked
            """,
            (
                dt.now().date(),
                total_apprentices,
                on_bil,
                on_track,
                fs_maths,
                fs_english,
                gateway_booked,
            ),
        )
        self.con.commit()
        res = self.cur.execute("SELECT * FROM stats")
        print(res.fetchall())

    def to_csv(self):
        for table in ["apprentices", "apprentice_projects", "projects"]:
            self.cur.execute(f"SELECT * FROM {table}")
            # cur.fetchall()
            with open(f"{table}.csv", "w") as f:
                w = csv.writer(f, lineterminator="\n")
                w.writerow([i[0] for i in self.cur.description])
                w.writerows(self.cur)

    def missing_projects(self):
        # TODO grab which projects are missing
        r = self.cur.execute("SELECT COUNT(*) FROM projects")
        sql = """
            SELECT 
                a.name, 
                (
                    SELECT COUNT(*)
                    FROM apprentice_projects as ap 
                    WHERE ap.apprentice_uuid=a.uuid
                ) as submission_count
                
            FROM apprentices as a
            WHERE submission_count < (SELECT COUNT(*) FROM projects)
        """
        self.cur.execute(sql)
        return self.cur.fetchall()

    def get_new_notes(self):
        self.cur.execute(
            """
            SELECT a.name, an.*
            FROM apprentice_notes as an, apprentices as a
            WHERE date > ?
            AND an.apprentice_uuid = a.uuid
            ORDER BY date DESC
        """,
            ("2024-10-01",),
        )
        return self.cur.fetchall()

    def get_unbooked_gateways(self):
        self.cur.execute(
            """
            SELECT name
            FROM apprentices
            WHERE gateway_booked = FALSE
            ORDER BY name ASC
        """
        )
        return self.cur.fetchall()
