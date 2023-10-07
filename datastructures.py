from dataclasses import dataclass
from typing import List, Optional

@dataclass
class CompletionData:
    state: int
    timecompleted: int
    overrideby: Optional[int]
    valueused: bool
    hascompletion: bool
    isautomatic: bool
    istrackeduser: bool
    uservisible: bool

@dataclass
class Content:
    fileurl: str
    filename: str
    filepath: str
    filesize: int
    timemodified: int
    mimetype: Optional[str] = None
    timecreated: Optional[int] = None
    isexternalfile: Optional[bool] = None


@dataclass
class Module:
    id: int
    name: str
    instance: int
    contextid: int
    visible: int
    uservisible: bool
    visibleoncoursepage: int
    modicon: str
    modname: str
    completion: int
    url: Optional[str] = None # Sometimes its missing, bc some courses write a short intro text at the beginning? 
    completiondata: Optional[CompletionData] = None
    contents: List[Content] = None 

@dataclass
class Section:
    id: int
    name: str
    visible: int
    section: int
    uservisible: bool
    modules: List[Module]


####### Container for courses

@dataclass
class RecentCourse:
    id: int
    fullname: str
    shortname: str
    idnumber: str
    summary: str
    summaryformat: int
    startdate: int
    enddate: int
    visible: bool
    fullnamedisplay: str
    viewurl: str
    courseimage: str
    progress: int
    hasprogress: bool
    isfavourite: bool
    hidden: bool
    timeaccess: int
    showshortname: bool
    coursecategory: str



########### Assignments


@dataclass
class Config:
    plugin: str
    subtype: str
    name: str
    value: str

@dataclass
class IntroAttachment:
    filename: str
    filepath: str
    filesize: int
    fileurl: str
    timemodified: int
    mimetype: str
    isexternalfile: bool

@dataclass
class Assignment:
    id: int
    cmid: int
    course: int
    name: str
    nosubmissions: int
    submissiondrafts: int
    sendnotifications: int
    sendlatenotifications: int
    sendstudentnotifications: int
    duedate: int
    allowsubmissionsfromdate: int
    grade: int
    timemodified: int
    completionsubmit: int
    cutoffdate: int
    gradingduedate: int
    teamsubmission: int
    requireallteammemberssubmit: int
    teamsubmissiongroupingid: int
    blindmarking: int
    hidegrader: int
    revealidentities: int
    attemptreopenmethod: str
    maxattempts: int
    markingworkflow: int
    markingallocation: int
    requiresubmissionstatement: int
    preventsubmissionnotingroup: int
    configs: List[Config]
    intro: str
    introformat: int
    introfiles: List
    introattachments: List[IntroAttachment]

@dataclass
class Course:
    id: int
    fullname: str
    shortname: str
    timemodified: int
    assignments: List[Assignment]


