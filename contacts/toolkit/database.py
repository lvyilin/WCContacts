import pyodbc
from datetime import datetime
from hashlib import sha256

SUCCESS_MSG = "Success."
EMPTY_MSG = "Values cannot be empty!"
CONTACT_EXISTED_MSG = "Contact already existed!"
OA_EXISTED_MSG = "You've already added this account!"
INVALID_OPERATION_MSG = "Invalid operation!"
WECHAT_ID_EXISTED_MSG = "Wechat ID has existed!"
PASSWORD_INCORRECT_MSG = "Username or password incorrect!"
UPDATE_CONTACT_FAILED_MSG = "Update contact failed!"
WECHAT_ID_INVALID = "Wechat id not existed!"
OA_INVALID = "Official account not existed!"
CANNOT_ADD_YOURSELF = "Cannot add yourself."


class User:
    def __init__(self, wechat_id, name, gender, region, whats_up, phone, email) -> None:
        self.wechat_id = wechat_id
        self.name = name
        self.gender = gender
        self.region = region
        self.whats_up = whats_up
        self.phone = phone
        self.email = email
        self.has_avatar = False


class UserAdminView:
    def __init__(self, wechat_id, name, banned, admin) -> None:
        self.wechat_id = wechat_id
        self.name = name
        self.banned = banned
        self.admin = admin


class Contact:
    def __init__(self, wechat_id, name, gender, region, whats_up, alias, tag, mobile, description, source) -> None:
        self.user = User(wechat_id, name, gender, region, whats_up, None, None)
        self.alias = alias
        self.tag = tag
        self.mobile = mobile
        self.description = description
        self.source = source


class OfficialAccount:
    def __init__(self, name, description):
        self.name = name
        self.description = description


class Group:
    def __init__(self, owner, name, notice, members) -> None:
        self.owner = owner
        self.name = name
        self.notice = notice
        self.members = members


def encrypt(s):
    return sha256(s.encode("utf8")).hexdigest()


class DBSession:
    def __init__(self) -> None:
        self.connection = None
        self.cursor = None
        try:
            self.connection = pyodbc.connect("Driver={SQL Server Native Client 11.0};Server=localhost;Database=Contacts;Trusted_Connection=yes;")
            self.cursor = self.connection.cursor()
        except Exception as e:
            print("Cannot open multiple session.")
            raise e

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        self.cursor.close()
        self.connection.close()

    def register(self, wechat_id, name, password: str):
        if wechat_id == '' or name == '' or password == '':
            return False, EMPTY_MSG
        self.cursor.execute("select * from Contacts.dbo.Users where wechat_id=?", (wechat_id,))
        if self.cursor.fetchone() is not None:
            return False, WECHAT_ID_EXISTED_MSG
        encrypt_pwd = encrypt(password)
        self.cursor.execute('insert into Contacts.dbo.Users(wechat_id, name, password,created_time) '
                            'values (?,?,?,CURRENT_TIMESTAMP)',
                            (wechat_id, name, encrypt_pwd))
        self.connection.commit()
        return True, SUCCESS_MSG

    def verify_user(self, wechat_id, password):
        encrypt_pwd = encrypt(password)
        self.cursor.execute("select id,name,gender,region,whats_up "
                            "from Contacts.dbo.Users where wechat_id=? and password=? and banned=0",
                            (wechat_id, encrypt_pwd))
        row = self.cursor.fetchone()
        if row is None:
            return None
        return row

    def verify_admin(self, wechat_id, password):
        encrypt_pwd = encrypt(password)
        self.cursor.execute("select id,name,gender,region,whats_up "
                            "from Contacts.dbo.Users where wechat_id=? and password=? and banned=0 and admin=1",
                            (wechat_id, encrypt_pwd))
        row = self.cursor.fetchone()
        if row is None:
            return None
        return row

    def verify_cookie(self, cookie):
        self.cursor.execute(
            "select user_id from Contacts.dbo.Cookies where cookie=? and valid=1 and expired_time>CURRENT_TIMESTAMP ",
            (cookie,))
        row = self.cursor.fetchone()
        if row is None:
            return None
        return row[0]

    def login(self, wechat_id, password):
        if wechat_id == '' or password == '':
            return False, EMPTY_MSG

        info = self.verify_user(wechat_id, password)
        if info is None:
            return False, PASSWORD_INCORRECT_MSG
        cookie = encrypt(wechat_id + str(datetime.now()))
        self.cursor.execute("insert into Contacts.dbo.Cookies(user_id, cookie, created_time, expired_time)"
                            " values(?,?,CURRENT_TIMESTAMP,DATEADD(day ,2, CURRENT_TIMESTAMP))",
                            (info[0], cookie))
        self.connection.commit()
        return True, cookie

    def change_password(self, wechat_id, password, new_password):
        info = self.verify_user(wechat_id, password)
        if info is not None:
            self.cursor.execute('update Contacts.dbo.Users set password=? where wechat_id=?',
                                (encrypt(new_password), wechat_id))
            self.connection.commit()
            return True, SUCCESS_MSG
        return False, PASSWORD_INCORRECT_MSG

    def get_profile(self, cookie):
        user_id = self.verify_cookie(cookie)
        if user_id is None:
            return False, INVALID_OPERATION_MSG
        self.cursor.execute("exec GetProfile @id=?", user_id)
        row = self.cursor.fetchone()
        user = User(row[0], row[1], row[2], row[3], row[4], row[5], row[6])
        return True, user

    def get_contacts(self, cookie):
        user_id = self.verify_cookie(cookie)
        if user_id is None:
            return False, INVALID_OPERATION_MSG
        self.cursor.execute("select wechat_id,name,gender,region,whats_up,alias,tag,"
                            "mobile,description,source "
                            "from Contacts.dbo.Contacts,Contacts.dbo.Users "
                            "where Contacts.id=? and Contacts.contact_id=Users.id",
                            (user_id,))
        results = self.cursor.fetchall()
        contacts = []
        for row in results:
            contact = Contact(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9])
            contacts.append(contact)
        return True, contacts

    def get_contact_detail(self, cookie, wechat_id):
        user_id = self.verify_cookie(cookie)
        if user_id is None:
            return False, INVALID_OPERATION_MSG

        self.cursor.execute(
            "select wechat_id,name,gender,region,whats_up,alias,tag,"
            "mobile,description,source "
            "from Contacts.dbo.Contacts,Contacts.dbo.Users "
            "where Contacts.id=? and Contacts.contact_id=Users.id and Users.wechat_id=?",
            (user_id, wechat_id))
        row = self.cursor.fetchone()
        contact = Contact(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9])
        return True, contact

    def add_contact(self, cookie, contact_wechat_id):
        user_id = self.verify_cookie(cookie)
        if user_id is None:
            return False, INVALID_OPERATION_MSG

        self.cursor.execute("select id from Contacts.dbo.Users where wechat_id=?",
                            (contact_wechat_id,))
        result = self.cursor.fetchone()
        if result is None:
            return False, WECHAT_ID_INVALID
        cid = result[0]
        if cid == user_id:
            return False, CANNOT_ADD_YOURSELF
        try:
            self.cursor.execute("exec AddContact @id=?, @cid=?",
                                (user_id, cid))
            self.connection.commit()
        except:
            return False, CONTACT_EXISTED_MSG
        return True, SUCCESS_MSG

    def delete_contact(self, cookie, contact_wechat_id):
        user_id = self.verify_cookie(cookie)
        if user_id is None:
            return False, INVALID_OPERATION_MSG

        try:
            self.cursor.execute("delete from Contacts.dbo.Contacts"
                                " where id=? and "
                                "contact_id=(select id from Contacts.dbo.Users where wechat_id=?)",
                                (user_id, contact_wechat_id))
            self.connection.commit()
        except:
            return False, CONTACT_EXISTED_MSG
        return True, SUCCESS_MSG

    def update_contact(self, cookie, contact_wechat_id, alias, tag, mobile, description, source):
        alias = alias if alias != '' else None
        tag = tag if tag != '' else None
        mobile = mobile if mobile != '' else None
        description = description if description != '' else None
        source = source if source != '' else None

        user_id = self.verify_cookie(cookie)
        if user_id is None:
            return False, INVALID_OPERATION_MSG
        try:
            self.cursor.execute("update Contacts.dbo.Contacts "
                                "set alias=?,tag=?,mobile=?,description=?,source=?"
                                " where id=? and contact_id=(select id from Contacts.dbo.Users where wechat_id=?)",
                                (alias, tag, mobile, description, source, user_id, contact_wechat_id))
            self.connection.commit()
        except Exception as e:
            print(e)
            return False, UPDATE_CONTACT_FAILED_MSG
        return True, SUCCESS_MSG

    def update_profile(self, cookie, name, gender, region, whats_up, phone, email):
        if name is None:
            return False, EMPTY_MSG
        name = name if name != '' else None
        region = region if region != '' else None
        whats_up = whats_up if whats_up != '' else None
        phone = phone if phone != '' else ''
        email = email if email != '' else ''

        user_id = self.verify_cookie(cookie)
        if user_id is None:
            return False, INVALID_OPERATION_MSG
        try:
            self.cursor.execute("select phone_id, email_id from Contacts.dbo.Users where Users.id=?",
                                (user_id,))
            row = self.cursor.fetchone()
            phone_id, email_id = row[0], row[1]
            if phone_id is not None:
                self.cursor.execute("update Contacts.dbo.Phones set phone=? where id=?", (phone, phone_id))
            else:
                self.cursor.execute("insert into Contacts.dbo.Phones(phone, validated) values (?,?)",
                                    (phone, False))
                self.connection.commit()
                self.cursor.execute("select id from Contacts.dbo.Phones where phone=?", (phone,))
                phone_id = self.cursor.fetchone()[0]
                self.cursor.execute("update Contacts.dbo.Users set phone_id=? where id=?", (phone_id, user_id))
            if email_id is not None:
                self.cursor.execute("update Contacts.dbo.Emails set email=? where id=?", (email, email_id))
            else:
                self.cursor.execute("insert into Contacts.dbo.Emails(email, validated) values (?,?);",
                                    (email, False))
                self.connection.commit()
                self.cursor.execute("select id from Contacts.dbo.Emails where email=?", (email,))
                email_id = self.cursor.fetchone()[0]
                self.cursor.execute("update Contacts.dbo.Users set email_id=? where id=?", (email_id, user_id))
            self.cursor.execute(
                "update Contacts.dbo.Users set name=?,gender=?,region=?,whats_up=?,email_id=?,phone_id=? "
                "where id=?", (name, gender, region, whats_up, email_id, phone_id, user_id))
            self.connection.commit()

        except Exception as e:
            print(e)
            return False, UPDATE_CONTACT_FAILED_MSG
        return True, SUCCESS_MSG

    def add_oa(self, cookie, oa_name):
        user_id = self.verify_cookie(cookie)
        if user_id is None:
            return False, INVALID_OPERATION_MSG

        self.cursor.execute("select id from Contacts.dbo.OfficialAccounts where name=?",
                            (oa_name,))
        result = self.cursor.fetchone()
        if result is None:
            return False, OA_INVALID
        oa_id = result[0]
        try:
            self.cursor.execute("insert into Contacts.dbo.Subscriptions values (?,?)",
                                (user_id, oa_id))
            self.connection.commit()
        except Exception as e:
            print(e)
            return False, OA_EXISTED_MSG
        return True, SUCCESS_MSG

    def get_oa(self, cookie):
        user_id = self.verify_cookie(cookie)
        if user_id is None:
            return False, INVALID_OPERATION_MSG
        self.cursor.execute("select name,description from Contacts.dbo.Subscriptions, Contacts.dbo.OfficialAccounts "
                            "where Subscriptions.id=? and OfficialAccounts.id=Subscriptions.oa_id", (user_id,))
        results = self.cursor.fetchall()
        oa = []
        for row in results:
            oa.append(OfficialAccount(row[0], row[1]))
        return True, oa

    def add_group(self, cookie, group_name, notice, user_list):
        user_id = self.verify_cookie(cookie)
        if user_id is None:
            return False, INVALID_OPERATION_MSG
        tmp = group_name.strip(' ')
        if tmp is "" or tmp is '"':
            group_name = "、".join(user_list)
        try:
            self.cursor.execute("exec AddGroup @name=?, @notice=?,@owner_id=?",
                                (group_name, notice, user_id))
            self.connection.commit()
            self.cursor.execute("select @@IDENTITY")
            row = self.cursor.fetchone()
            group_id = row[0]
            self.cursor.execute("insert into Contacts.dbo.GroupMembers values (?,?)",
                                (group_id, user_id))
            for w_id in user_list:
                self.cursor.execute("exec AddGroupMember @group_id=?, @wechat_id=?", (group_id, w_id))
            self.connection.commit()
        except Exception as e:
            print(e)
            raise e
        return True, SUCCESS_MSG

    def delete_group(self, cookie, group_name):
        user_id = self.verify_cookie(cookie)
        if user_id is None:
            return False, INVALID_OPERATION_MSG
        try:
            self.cursor.execute("delete from Contacts.dbo.Groups where owner_id=? and name=?",
                                (user_id, group_name))
            self.connection.commit()
        except Exception as e:
            print(e)
            raise e
        return True, SUCCESS_MSG

    def get_groups(self, cookie):
        user_id = self.verify_cookie(cookie)
        if user_id is None:
            return False, INVALID_OPERATION_MSG
        try:
            self.cursor.execute("select Groups.id,Groups.name,Groups.notice, Users.wechat_id "
                                "from Contacts.dbo.Groups ,Contacts.dbo.Users, Contacts.dbo.GroupMembers "
                                "where Groups.owner_id=Users.id and "
                                "Groups.id=GroupMembers.id and "
                                "GroupMembers.user_id=?",
                                (user_id,))
            rows = self.cursor.fetchall()
            groups = []
            for row in rows:
                group_name = row[1]
                group_notice = row[2]
                group_owner = row[3]
                self.cursor.execute("select Users.wechat_id from Contacts.dbo.GroupMembers, Contacts.dbo.Users"
                                    " where GroupMembers.user_id=Users.id and GroupMembers.id=?", (row[0]))
                members = [m[0] for m in self.cursor.fetchall()]
                groups.append(Group(group_owner, group_name, group_notice, members))

            return True, groups
        except Exception as e:
            print(e)
            raise e

    def admin_login(self, admin_id, password):
        if admin_id == '' or password == '':
            return False, EMPTY_MSG

        info = self.verify_admin(admin_id, password)
        if info is None:
            return False, INVALID_OPERATION_MSG
        cookie = encrypt(admin_id + str(datetime.now()))
        self.cursor.execute("insert into Contacts.dbo.Cookies(user_id, cookie, created_time, expired_time)"
                            " values(?,?,CURRENT_TIMESTAMP,DATEADD(day ,2, CURRENT_TIMESTAMP))",
                            (info[0], cookie))
        self.connection.commit()
        return True, cookie

    def admin_get_users(self, cookie):
        user_id = self.verify_cookie(cookie)
        if user_id is None:
            return False, INVALID_OPERATION_MSG
        self.cursor.execute("select * "
                            "from Contacts.dbo.UserAdminView ")
        results = self.cursor.fetchall()
        contacts = []
        for row in results:
            contact = UserAdminView(row[0], row[1], row[2], row[3])
            contacts.append(contact)
        return True, contacts

    def admin_op(self, cookie, results):
        user_id = self.verify_cookie(cookie)
        if user_id is None:
            return False, INVALID_OPERATION_MSG
        try:
            for item in results:
                wechat_id = item['name']
                banned = item['bannedChecked']
                admin = item['adminChecked']
                self.cursor.execute("update Contacts.dbo.Users set banned=?, admin=? where wechat_id=?",
                                    (banned, admin, wechat_id))
            self.connection.commit()
            return True, SUCCESS_MSG
        except Exception as e:
            print(e)
            raise e

    def admin_new_oa(self, cookie, oa_name, oa_desc):
        user_id = self.verify_cookie(cookie)
        if user_id is None:
            return False, INVALID_OPERATION_MSG
        if oa_name is "" or oa_desc is "":
            return False, EMPTY_MSG
        try:
            self.cursor.execute("insert into Contacts.dbo.OfficialAccounts(name, description) values (?,?)",
                                (oa_name, oa_desc))
            self.connection.commit()
            return True, SUCCESS_MSG
        except Exception as e:
            print(e)
            raise e

    def search(self, cookie, keyword):
        user_id = self.verify_cookie(cookie)
        if user_id is None:
            return False, INVALID_OPERATION_MSG
        if keyword is None or keyword == "":
            return False, EMPTY_MSG
        keyword = "%{}%".format(keyword)
        results = {'contacts': [], "officialAccounts": [], "groups": []}
        try:
            self.cursor.execute("select wechat_id, name, alias from Contacts.dbo.Users,Contacts.dbo.Contacts "
                                "where Contacts.id=? and Contacts.contact_id=Users.id "
                                "and (wechat_id like ? or name like ? or alias like ?)",
                                (user_id, keyword, keyword, keyword))
            rows = self.cursor.fetchall()
            for row in rows:
                results['contacts'].append({'name': row[1], 'wechat_id': row[0], 'alias': row[2]})

            self.cursor.execute("select name from Contacts.dbo.OfficialAccounts,Contacts.dbo.Subscriptions "
                                "where Subscriptions.id=? and OfficialAccounts.id=Subscriptions.oa_id "
                                "and name like ? ",
                                (user_id, keyword))
            rows = self.cursor.fetchall()
            for row in rows:
                results['officialAccounts'].append({'name': row[0]})

            self.cursor.execute("select name from Contacts.dbo.Groups,Contacts.dbo.GroupMembers "
                                "where Groups.id=GroupMembers.id and GroupMembers.user_id=? and"
                                " Groups.name like ? ",
                                (user_id, keyword))
            rows = self.cursor.fetchall()
            for row in rows:
                results['groups'].append({'name': row[0]})
            return True, results
        except Exception as e:
            print(e)
            raise e


def main():
    import string
    import random
    import time

    def str_generator(size, chars=string.ascii_uppercase + string.digits):
        return ''.join(random.choice(chars) for _ in range(size))

    with DBSession() as sess:
        # for i in range(100000):
        #     sess.register(str_generator(10), str_generator(10), '123456')
        t_with_index, t_without_index = [], []
        wids, names = [], []
        num = 1000
        sess.cursor.execute("select top 1000 wechat_id, name from Contacts.dbo.Users order by NEWID()")
        for row in sess.cursor.fetchall():
            wids.append(row[0])
            names.append(row[1])
        for i in range(num):
            row = sess.cursor.fetchone()
            start = time.time()
            sess.cursor.execute("select * from Contacts.dbo.Users where name=?", (names[i],))
            t_without_index.append(time.time() - start)
            start = time.time()
            sess.cursor.execute("select * from Contacts.dbo.Users where wechat_id=?", (wids[i],))
            t_with_index.append(time.time() - start)
        print("Time spent without index: {}s".format(sum(t_without_index) / len(t_without_index)))
        print("Time spent with index: {}s".format(sum(t_with_index) / len(t_with_index)))


if __name__ == '__main__':
    main()
