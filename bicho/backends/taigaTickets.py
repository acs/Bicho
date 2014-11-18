# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Bitergia
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
# Authors:  Alvaro del Castillo <acs@bitergia.com>
#

from bicho.config import Config

from bicho.backends import Backend
from bicho.utils import create_dir
from bicho.db.database import DBIssue, DBBackend, get_database
from bicho.common import Tracker, Issue, People, Change

from dateutil.parser import parse
from datetime import datetime

import errno
import json
import os
import pprint
import random
import sys
import time
import traceback
import urllib
import urllib2
import feedparser
import logging

from storm.locals import DateTime, Desc, Int, Reference, Unicode, Bool


class DBTaigaTicketsIssueExt(object):
    __storm_table__ = 'issues_ext_taigaTickets'

    id = Int(primary=True)
    tags = Unicode()
    version = Unicode()
    type = Unicode()
    project = Unicode()
    milestone = Unicode()
    comment = Unicode()
    mod_date = DateTime()
    finished_date = DateTime()
    issue_id = Int()


    issue = Reference(issue_id, DBIssue.id)

    def __init__(self, issue_id):
        self.issue_id = issue_id


class DBTaigaTicketsIssueExtMySQL(DBTaigaTicketsIssueExt):
    """
    MySQL subclass of L{DBTaigaTicketsIssueExt}
    """

    # If the table is changed you need to remove old from database
    __sql_table__ = 'CREATE TABLE IF NOT EXISTS issues_ext_taigaTickets ( \
                    id INTEGER NOT NULL AUTO_INCREMENT, \
                    tags TEXT, \
                    type TEXT, \
                    version TEXT, \
                    project TEXT, \
                    milestone TEXT, \
                    comment TEXT, \
                    finished_date DATETIME, \
                    mod_date DATETIME, \
                    issue_id INTEGER NOT NULL, \
                    PRIMARY KEY(id), \
                    FOREIGN KEY(issue_id) \
                    REFERENCES issues (id) \
                    ON DELETE CASCADE \
                    ON UPDATE CASCADE \
                     ) ENGINE=MYISAM;'


class DBTaigaTicketsBackend(DBBackend):
    """
    Adapter for TaigaTickets backend.
    """
    def __init__(self):
        self.MYSQL_EXT = [DBTaigaTicketsIssueExtMySQL]

    def insert_issue_ext(self, store, issue, issue_id):

        newIssue = False

        try:
            db_issue_ext = store.find(DBTaigaTicketsIssueExt,
                                      DBTaigaTicketsIssueExt.issue_id == issue_id).one()
            if not db_issue_ext:
                newIssue = True
                db_issue_ext = DBTaigaTicketsIssueExt(issue_id)
                #db_issue_ext = DBSourceForgeIssueExt(issue.category, issue.group, issue_id)

            db_issue_ext.tags = unicode(issue.tags)
            db_issue_ext.version = unicode(issue.version)
            db_issue_ext.type = unicode(issue.type)
            db_issue_ext.project = unicode(issue.project)
            db_issue_ext.milestone = unicode(issue.milestone)
            db_issue_ext.comment = unicode(issue.comment)
            db_issue_ext.finished_date = issue.finished_date
            db_issue_ext.mod_date = issue.mod_date

            if newIssue is True:
                store.add(db_issue_ext)

            store.flush()
            return db_issue_ext
        except:
            store.rollback()
            raise

    def insert_change_ext(self, store, change, change_id):
        """
        Does nothing
        """
        pass

    def get_last_modification_date(self, store, tracker_id):
        # get last modification date (day) stored in the database
        # select date_last_updated as date from issues_ext_taigaTickets order by date
        result = store.find(DBTaigaTicketsIssueExt)
        aux = result.order_by(Desc(DBTaigaTicketsIssueExt.mod_date))[:1]

        for entry in aux:
            return entry.mod_date.strftime('%Y-%m-%dT%H:%M:%SZ')

        return None


class TaigaTicketsIssue(Issue):
    """
    Ad-hoc Issue extension for taigaTickets's issue
    """
    def __init__(self, issue, type, summary, desc, submitted_by, submitted_on):
        Issue.__init__(self, issue, type, summary, desc, submitted_by,
                       submitted_on)

        if False:
            self.tags = None
            self.version = None
            self.type = None
            self.project = None
            self.milestone = None
            self.comment  = None
            self.mod_date = None
            self.finished_date = None

class TaigaTickets():
    """
    TaigaTickets backend
    """

    project_test_file = None
    safe_delay = 5

    def __init__(self):
        self.delay = Config.delay

    def _convert_to_datetime(self, str_date):
        """
        Returns datetime object from string
        """
        return parse(str_date).replace(tzinfo=None)

    def analyze_bug(self, issue_data):
        issue = self.parse_bug(issue_data)
        return issue

    def parse_bug(self, issue_taigaTickets):
        # [u'comment', u'owner', u'id', u'is_closed', u'subject', u'finished_date', u'modified_date', 
        # u'votes', u'severity', u'description_html', u'priority', u'version', u'generated_user_stories', 
        # u'blocked_note_html', u'type', u'status', u'description', u'tags', u'assigned_to', u'blocked_note', 
        # u'milestone', u'is_blocked', u'watchers', u'ref', u'project', u'created_date']

        people = People(issue_taigaTickets["owner"])
        people.set_name(issue_taigaTickets["owner"])

        issue = TaigaTicketsIssue(issue_taigaTickets["id"],
                            "ticket",
                            issue_taigaTickets["subject"],
                            issue_taigaTickets["description"],
                            people,
                            self._convert_to_datetime(issue_taigaTickets["created_date"]))
        people = People(issue_taigaTickets["assigned_to"])
        people.set_name(issue_taigaTickets["assigned_to"])
        issue.assigned_to = people
        issue.status = issue_taigaTickets["status"]
        # No information from TaigaTickets for this fields
        issue.resolution = None
        issue.priority = issue_taigaTickets["priority"]

        # Extended attributes
        issue.tags = str(issue_taigaTickets["tags"])
        issue.version = issue_taigaTickets["version"]
        issue.type = str(issue_taigaTickets["type"])
        issue.project = str(issue_taigaTickets["project"])
        issue.milestone = str(issue_taigaTickets["milestone"])
        issue.comment  = str(issue_taigaTickets["comment"])
        issue.mod_date = self._convert_to_datetime(issue_taigaTickets["modified_date"])
        if issue_taigaTickets["finished_date"] is not None:
            issue.finished_date = self._convert_to_datetime(issue_taigaTickets["finished_date"])
        else: issue.finished_date = None

        return issue

    def remove_unicode(self, str):
        """
        Cleanup u'' chars indicating a unicode string
        """
        if (str.startswith('u\'') and str.endswith('\'')):
            str = str[2:len(str) - 1]
        return str

    def run(self):
        """
        """
        logging.info("Running Bicho with delay of %s seconds" % (str(self.delay)))

        # limit=-1 is NOT recognized as 'all'.  500 is a reasonable limit. - taigaTickets code
        issues_per_query = 500
        start_page = 0

        bugs = []
        bugsdb = get_database(DBTaigaTicketsBackend())

        # still useless in taigaTickets
        bugsdb.insert_supported_traker("taigaTickets", "beta")
        trk = Tracker(Config.url, "taigaTickets", "beta")
        dbtrk = bugsdb.insert_tracker(trk)

#        last_mod_date = bugsdb.get_last_modification_date(tracker_id=dbtrk.id)
#
#        # Date before the first ticket
#        time_window_start = "1900-01-01T00:00:00Z"
#        time_window_end = datetime.now().isoformat() + "Z"
#
#        if last_mod_date:
#            time_window_start = last_mod_date
#            logging.info("Last bugs analyzed were modified on: %s" % last_mod_date)
#
#        time_window = time_window_start + " TO  " + time_window_end

        # self.url_issues = Config.url + "/search/?limit=1"
        # self.url_issues += "&q="
        # A time range with all the tickets
        # self.url_issues += urllib.quote("mod_date_dt:[" + time_window + "]")
        self.url_api = Config.url
        self.url_api += "/api/v1/"
        self.url_projects =  self.url_api + "/projects"
        self.url_issues =  self.url_api + "/issues"
        self.url_users =  self.url_api + "/users"
        logging.info("URL for getting projects " + self.url_projects)

        # Add GET HEADER
        # "Authorization: Bearer eyJ1c2VyX2lkIjoxfQ:1XqfAF:wck1FLZscHNeHvENMMTwKMrumR4"
        # f = urllib.urlopen(self.url_projects)
        auth_token = "eyJ1c2VyX2lkIjoxfQ:1XqfAF:wck1FLZscHNeHvENMMTwKMrumR4"

#        request = urllib2.Request(self.url_projects, headers={"Authorization":"Bearer " + auth_token})
#        f = urllib2.urlopen(request)
#        projects = json.loads(f.read())
#        request = urllib2.Request(self.url_users, headers={"Authorization":"Bearer " + auth_token})
#        f = urllib2.urlopen(request)
#        users = json.loads(f.read())

        request = urllib2.Request(self.url_issues, headers={"Authorization":"Bearer " + auth_token})
        f = urllib2.urlopen(request)
        issues = json.loads(f.read())


        total_issues = len(issues)
        total_pages = total_issues / issues_per_query
        print("Number of tickets: " + str(total_issues))

        if total_issues == 0:
            logging.info("No bugs found. Did you provide the correct url?")
            sys.exit(0)
        remaining = total_issues

        # print "ETA ", (total_issues * Config.delay) / (60), "m (", (total_issues * Config.delay) / (60 * 60), "h)"

        for issue in issues:
            try:
                issue_data = self.analyze_bug(issue)
                if issue_data is None:
                    continue
                bugsdb.insert_issue(issue_data, dbtrk.id)
            except Exception, e:
                logging.error("Error in function analyze_bug " + str(issue['id']))
                traceback.print_exc(file=sys.stdout)
            except UnicodeEncodeError:
                logging.error("UnicodeEncodeError: the issue %s couldn't be stored"
                         % (issue_data.issue))
        start_page += 1

        logging.info("Done. Bugs analyzed:" + str(total_issues - remaining))

Backend.register_backend('taigaTickets', TaigaTickets)