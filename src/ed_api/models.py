"""Data models for ed-api."""

from dataclasses import dataclass, field
from datetime import datetime


def _parse_dt(s: str | None) -> datetime | None:
    if not s:
        return None
    # Ed uses ISO format with Z suffix
    s = s.replace("Z", "+00:00")
    return datetime.fromisoformat(s)


@dataclass
class UserSummary:
    id: int
    name: str
    role: str  # "student", "staff", "admin"

    @property
    def is_staff(self) -> bool:
        return self.role in ("staff", "admin")


@dataclass
class UserInfo:
    id: int
    name: str
    email: str
    role: str
    avatar: str | None = None


@dataclass
class Course:
    id: int
    code: str
    name: str
    year: str
    session: str
    status: str  # "active" or "archived"


@dataclass
class CourseEnrollment:
    course: Course
    role: str  # "student", "staff", "admin"


@dataclass
class ParsedUserInfo:
    user: UserInfo
    courses: list[CourseEnrollment]


@dataclass
class CourseUser:
    id: int
    name: str
    email: str
    role: str
    course_role: str

    @property
    def is_staff(self) -> bool:
        return self.course_role in ("staff", "admin")


@dataclass
class Comment:
    id: int
    thread_id: int
    parent_id: int | None
    user_id: int
    author: UserSummary | None
    type: str  # "comment" or "answer"
    content: str  # Ed XML (raw)
    is_endorsed: bool
    is_anonymous: bool
    is_private: bool
    created_at: datetime | None
    vote_count: int = 0
    replies: list["Comment"] = field(default_factory=list)


@dataclass
class Thread:
    id: int
    course_id: int
    number: int
    type: str  # "question", "post", "announcement"
    title: str
    content: str  # Ed XML (raw)
    category: str
    subcategory: str | None
    author: UserSummary
    is_pinned: bool
    is_private: bool
    is_locked: bool
    is_endorsed: bool
    is_answered: bool
    is_staff_answered: bool
    is_student_answered: bool
    created_at: datetime | None
    updated_at: datetime | None
    view_count: int = 0
    vote_count: int = 0
    reply_count: int = 0


@dataclass
class ThreadDetail(Thread):
    comments: list[Comment] = field(default_factory=list)
    users: dict[int, UserSummary] = field(default_factory=dict)

    @property
    def is_unanswered(self) -> bool:
        return len(self.comments) == 0

    @property
    def has_staff_response(self) -> bool:
        for c in self.comments:
            author = self.users.get(c.user_id)
            if author and author.is_staff:
                return True
        return False

    @property
    def has_student_only(self) -> bool:
        return len(self.comments) > 0 and not self.has_staff_response

    @property
    def needs_followup(self) -> bool:
        if not self.has_staff_response:
            return False
        last_staff_idx = -1
        for i, c in enumerate(self.comments):
            author = self.users.get(c.user_id)
            if author and author.is_staff:
                last_staff_idx = i
        # Student commented after last staff response
        return last_staff_idx < len(self.comments) - 1


# --- Parse functions ---

def parse_thread(raw: dict) -> Thread:
    user_data = raw.get("user", {})
    author = UserSummary(
        id=user_data.get("id", 0),
        name=user_data.get("name", "Unknown"),
        role=user_data.get("course_role") or user_data.get("role", "student"),
    )
    return Thread(
        id=raw["id"],
        course_id=raw.get("course_id", 0),
        number=raw.get("number", 0),
        type=raw.get("type", "post"),
        title=raw.get("title", ""),
        content=raw.get("content", ""),
        category=raw.get("category", ""),
        subcategory=raw.get("subcategory") or None,
        author=author,
        is_pinned=raw.get("is_pinned", False),
        is_private=raw.get("is_private", False),
        is_locked=raw.get("is_locked", False),
        is_endorsed=raw.get("is_endorsed", False),
        is_answered=raw.get("is_answered", False),
        is_staff_answered=raw.get("is_staff_answered", False),
        is_student_answered=raw.get("is_student_answered", False),
        created_at=_parse_dt(raw.get("created_at")),
        updated_at=_parse_dt(raw.get("updated_at")),
        view_count=raw.get("view_count", 0),
        vote_count=raw.get("vote_count", 0),
        reply_count=raw.get("reply_count", 0),
    )


def parse_comment(raw: dict, users: dict[int, UserSummary] | None = None) -> Comment:
    author = None
    if users and raw.get("user_id") in users:
        author = users[raw["user_id"]]
    replies = [parse_comment(r, users) for r in raw.get("comments", [])]
    return Comment(
        id=raw["id"],
        thread_id=raw.get("thread_id", 0),
        parent_id=raw.get("parent_id"),
        user_id=raw.get("user_id", 0),
        author=author,
        type=raw.get("type", "comment"),
        content=raw.get("content", ""),
        is_endorsed=raw.get("is_endorsed", False),
        is_anonymous=raw.get("is_anonymous", False),
        is_private=raw.get("is_private", False),
        created_at=_parse_dt(raw.get("created_at")),
        vote_count=raw.get("vote_count", 0),
        replies=replies,
    )


def parse_thread_detail(raw: dict) -> ThreadDetail:
    thread_data = raw.get("thread", raw)
    users_list = raw.get("users", [])
    users = {}
    for u in users_list:
        users[u["id"]] = UserSummary(
            id=u["id"],
            name=u.get("name", "Unknown"),
            role=u.get("course_role") or u.get("role", "student"),
        )

    base = parse_thread(thread_data)
    # Fix author from users dict if parse_thread couldn't find it
    thread_user_id = thread_data.get("user_id", 0)
    if base.author.name == "Unknown" and thread_user_id in users:
        base = Thread(**{**base.__dict__, "author": users[thread_user_id]})

    answers = [parse_comment(a, users) for a in thread_data.get("answers", [])]
    comments = [parse_comment(c, users) for c in thread_data.get("comments", [])]
    all_comments = answers + comments

    return ThreadDetail(
        id=base.id,
        course_id=base.course_id,
        number=base.number,
        type=base.type,
        title=base.title,
        content=base.content,
        category=base.category,
        subcategory=base.subcategory,
        author=base.author,
        is_pinned=base.is_pinned,
        is_private=base.is_private,
        is_locked=base.is_locked,
        is_endorsed=base.is_endorsed,
        is_answered=base.is_answered,
        is_staff_answered=base.is_staff_answered,
        is_student_answered=base.is_student_answered,
        created_at=base.created_at,
        updated_at=base.updated_at,
        view_count=base.view_count,
        vote_count=base.vote_count,
        reply_count=base.reply_count,
        comments=all_comments,
        users=users,
    )


@dataclass
class Slide:
    id: int
    lesson_id: int
    course_id: int
    type: str  # "document", "quiz", "code", "pdf", "video", "webpage", "html"
    title: str
    index: int
    is_hidden: bool
    content: str  # Ed XML or HTML
    video_url: str | None  # for type=="video"
    file_url: str | None  # for type=="pdf" etc
    url: str | None  # for type=="webpage"
    created_at: datetime | None


@dataclass
class Lesson:
    id: int
    course_id: int
    module_id: int | None
    title: str
    lesson_number: int
    is_hidden: bool
    is_unlisted: bool
    created_at: datetime | None
    available_at: datetime | None
    due_at: datetime | None
    slides: list[Slide] = field(default_factory=list)


@dataclass
class Module:
    id: int
    name: str
    course_id: int


# --- Lesson/Slide parse functions ---

def parse_slide(raw: dict) -> Slide:
    return Slide(
        id=raw["id"],
        lesson_id=raw.get("lesson_id", 0),
        course_id=raw.get("course_id", 0),
        type=raw.get("type", "document"),
        title=raw.get("title", ""),
        index=raw.get("index", 0),
        is_hidden=raw.get("is_hidden", False),
        content=raw.get("content", ""),
        video_url=raw.get("video_url"),
        file_url=raw.get("file_url"),
        url=raw.get("url"),
        created_at=_parse_dt(raw.get("created_at")),
    )


def parse_lesson(raw: dict) -> Lesson:
    slides = [parse_slide(s) for s in raw.get("slides", [])]
    return Lesson(
        id=raw["id"],
        course_id=raw.get("course_id", 0),
        module_id=raw.get("module_id"),
        title=raw.get("title", ""),
        lesson_number=raw.get("lesson_number", 0),
        is_hidden=raw.get("is_hidden", False),
        is_unlisted=raw.get("is_unlisted", False),
        created_at=_parse_dt(raw.get("created_at")),
        available_at=_parse_dt(raw.get("available_at")),
        due_at=_parse_dt(raw.get("due_at")),
        slides=slides,
    )


def parse_module(raw: dict) -> Module:
    return Module(
        id=raw["id"],
        name=raw.get("name", ""),
        course_id=raw.get("course_id", 0),
    )


def parse_user_info(raw: dict) -> ParsedUserInfo:
    u = raw["user"]
    user = UserInfo(
        id=u["id"],
        name=u["name"],
        email=u["email"],
        role=u.get("role", "user"),
        avatar=u.get("avatar"),
    )
    courses = []
    for entry in raw.get("courses", []):
        c = entry["course"]
        course = Course(
            id=c["id"],
            code=c.get("code", ""),
            name=c.get("name", ""),
            year=c.get("year", ""),
            session=c.get("session", ""),
            status=c.get("status", "active"),
        )
        role = entry.get("role", {}).get("role", "student")
        courses.append(CourseEnrollment(course=course, role=role))
    return ParsedUserInfo(user=user, courses=courses)
