import argparse
from datetime import datetime as dt
import pandas as pd

from scraper import Scraper

parser = argparse.ArgumentParser(description="Scrapes data")
parser.add_argument("-n", "--no-input", action="store_true")


def main():
    s = Scraper()
    if (
        input("Press y to kill existing Chrome windows and fetch latest data.\n> ")
        .strip()
        .lower()
        == "y"
    ):
        print("Return here to continue once Chrome is open.")
        s.initial_update()
    while True:
        print("0 - Exit")
        print("1 - Export data to csv")
        print("2 - Full apprentice update")
        print("3 - Update stats to DB")
        print("4 - Interact with data")
        print("5 - Get project data")
        print("6 - Show missing project submissions")
        print("7 - Show notes added since last update")
        print("8 - Show unbooked gateways")

        try:
            choice = int(input("> "))
        except ValueError:
            choice = None
        while choice not in range(8):
            break

        if choice == 0:
            exit(0)
        elif choice == 1:
            print(">>> Dumping all tables to .csv...", end="")
            s.to_csv()
            print(" done!")
            print(
                ">>> If an update wasn't run before this, this was the latest saved data"
            )
            input(">>> Press any key to return to menu")
        elif choice == 2:
            print(">>> Full apprentice data update")
            print(">>> This will take several minutes to process")
            print(">>> All other Chrome windows will be force closed before")
            print(">>> Press any key to continue")
            input()
            s.get_apprentices(full_export=True)
            s.save_notes_to_db()
            print(">>> Done!")
            input(">>> Press any key to return to menu")
        elif choice == 3:
            s.create_stats()
            print(">>> Done!")
            input(">>> Press any key to return to menu")
        elif choice == 4:
            print(
                ">>> Data loaded into dataframe with the variables: apprentices_df, notes_df and projects_df. Pandas is available as pd"
            )
            print()
            apprentices_df = pd.read_csv("./apprentices.csv")
            notes_df = pd.read_csv("./notes.csv", encoding="utf-8")
            projects_df = pd.read_csv("./projects.csv")
            notes_df = pd.read_csv("./notes.csv")
            import code

            code.interact(local=locals())
        elif choice == 5:
            print(">>> Getting project data...", end="")
            s.get_projects()
            s.save_projects_to_db()
            print(" done")
            input(">>> Press any key to return to menu")
        elif choice == 6:
            if len(s.projects) == 0:
                print("Please update projects first")
            else:
                print(
                    ">>> The following apprentices may be missing a project submission:"
                )
                for row in s.missing_projects():
                    print(f"{row[0]}\t\t\t{row[1]} submission(s)")
            input(">>> Press any key to return to menu")
        elif choice == 7:
            print(f"Showing notes since {s.last_updated}\n")
            for note in s.get_new_notes():
                date = str(dt.strptime(note[3], "%Y-%m-%d %H:%M:%S").date())
                print(f"Apprentice: {note[0]}")
                print(f"From: {note[2]} {date}")
                print(f"{note[4]}")
                print(f"{note[5]} - {note[6]}")
                print()
            input(">>> Press any key to return to menu")
        elif choice == 8:
            print("Apprentices who haven't booked a gateway:")
            for apprentice in s.get_unbooked_gateways():
                print(f"* {apprentice[0]}")
            input(">>> Press any key to return to menu")


def update():
    s = Scraper()
    s.get_apprentices(full_export=True)
    s.get_apprentice_updates()
    s.get_projects()


if __name__ == "__main__":
    args = parser.parse_args()
    automated = args.no_input
    if automated:
        update()
    else:
        main()
