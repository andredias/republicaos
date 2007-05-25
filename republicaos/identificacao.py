from datetime import datetime
from sqlalchemy import *
from turbogears.database import metadata, session
from sqlalchemy.ext.assignmapper import assign_mapper
from turbogears import identity



# The identity schema.
visits_table = Table('visit', metadata,
    Column('visit_key', String(40), primary_key=True),
    Column('created', DateTime, nullable=False, default=datetime.now),
    Column('expiry', DateTime)
)

visit_identity_table = Table('visit_identity', metadata,
    Column('visit_key', String(40), primary_key=True),
    Column('user_id', Integer, ForeignKey('tg_user.user_id'), index=True)
)

groups_table = Table('tg_group', metadata,
    Column('group_id', Integer, primary_key=True),
    Column('group_name', Unicode(16), unique=True),
    Column('display_name', Unicode(255)),
    Column('created', DateTime, default=datetime.now)
)

users_table = Table('tg_user', metadata,
    Column('user_id', Integer, primary_key=True),
    Column('user_name', Unicode(16), unique=True),
    Column('email_address', Unicode(255), unique=True),
    Column('display_name', Unicode(255)),
    Column('password', Unicode(40)),
    Column('created', DateTime, default=datetime.now)
)

permissions_table = Table('permission', metadata,
    Column('permission_id', Integer, primary_key=True),
    Column('permission_name', Unicode(16), unique=True),
    Column('description', Unicode(255))
)

user_group_table = Table('user_group', metadata,
    Column('user_id', Integer, ForeignKey('tg_user.user_id')),
    Column('group_id', Integer, ForeignKey('tg_group.group_id'))
)

group_permission_table = Table('group_permission', metadata,
    Column('group_id', Integer, ForeignKey('tg_group.group_id')),
    Column('permission_id', Integer, ForeignKey('permission.permission_id'))
)


class Visit(object):
    """
    A visit to your site
    """
    def lookup_visit(cls, visit_key):
        return Visit.get(visit_key)
    lookup_visit = classmethod(lookup_visit)

class VisitIdentity(object):
    """
    A Visit that is link to a User object
    """
    pass

class Group(object):
    """
    An ultra-simple group definition.
    """
    pass

class User(object):
    """
    Reasonably basic User definition. Probably would want additional
    attributes.
    """
    def permissions(self):
        perms = set()
        for g in self.groups:
            perms = perms | set(g.permissions)
        return perms
    permissions = property(permissions)

    def by_email_address(klass, email): 
        """
        A class method that can be used to search users
        based on their email addresses since it is unique.
        """
        return klass.get_by(users_table.c.email_address==email) 

    by_email_address = classmethod(by_email_address)

    def by_user_name(klass, username):
        """
        A class method that permits to search users
        based on their user_name attribute.
        """
        return klass.get_by(users_table.c.user_name==username)
    by_user_name = classmethod(by_user_name)

class Permission(object):
    """
    A relationship that determines what each Group can do
    """
    pass

assign_mapper(session.context, Visit, visits_table)
assign_mapper(session.context, VisitIdentity, visit_identity_table,
          properties=dict(users=relation(User, backref='visit_identity')))
assign_mapper(session.context, User, users_table)
assign_mapper(session.context, Group, groups_table,
          properties=dict(users=relation(User, secondary=user_group_table, backref='groups')))
assign_mapper(session.context, Permission, permissions_table,
          properties=dict(groups=relation(Group, secondary=group_permission_table, backref='permissions')))

