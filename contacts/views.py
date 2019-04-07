from django.shortcuts import render, redirect
from django.http import JsonResponse
from .toolkit import database
from .forms import LoginForm, RegisterForm, ContactForm, AddContactForm, ChangePasswordForm, ChangeProfileForm, \
    AddOAForm, AdminForm
from django.contrib import messages
import json

NOT_LOGIN_MSG = "Login first :)"


def login(request):
    if request.method == 'GET':
        return render(request, "login.html")
    elif request.method == 'POST':
        form = LoginForm(request.POST)
        with database.DBSession() as sess:
            ok, result = sess.login(form['wechat_id'].value(), form['password'].value())
            if not ok:
                messages.info(request, result)
                return redirect("/")
        # return contacts(request, form['wechat_id'].value())
        return redirect("/contacts/%s" % result)


def admin_login(request):
    if request.method == 'GET':
        return render(request, "admin_login.html")
    elif request.method == 'POST':
        form = AdminForm(request.POST)
        with database.DBSession() as sess:
            ok, result = sess.admin_login(form['admin_id'].value(), form['password'].value())
            if not ok:
                messages.info(request, result)
                return redirect("/admin_login")
        # return contacts(request, form['wechat_id'].value())
        return redirect("/admin/%s" % result)


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        with database.DBSession() as sess:
            ok, result = sess.register(form['wechat_id'].value(), form['name'].value(), form['password'].value())
            messages.info(request, result)
    return redirect("/")


def change_password(request):
    if request.method == 'POST':
        form = ChangePasswordForm(request.POST)
        with database.DBSession() as sess:
            ok, result = sess.change_password(form['wechat_id'].value(),
                                              form['password'].value(),
                                              form['new_password'].value())
            return JsonResponse({'msg': result})


def contacts(request, passkey):
    if passkey is None:
        messages.info(request, NOT_LOGIN_MSG)
        return redirect("/")

    with database.DBSession() as sess:
        ok, result = sess.get_contacts(passkey)
        if not ok:
            messages.info(request, result)
            return redirect("/")
        ok, my_profile = sess.get_profile(passkey)
        ok, oa = sess.get_oa(passkey)
        ok, groups = sess.get_groups(passkey)
    return render(request, "contacts.html", {'contacts': result, 'profile': my_profile, 'oa': oa, 'groups': groups})


def detail(request, passkey, wechat_id):
    with database.DBSession() as sess:
        ok, result = sess.get_contact_detail(passkey, wechat_id)
        if not ok:
            messages.info(request, result)
            return redirect("/")
        # class to dict
        result_dict = result.__dict__
        result_dict['user'] = result_dict['user'].__dict__
    return JsonResponse({'contact': result_dict})


def profile(request, passkey):
    with database.DBSession() as sess:
        ok, result = sess.get_profile(passkey)
        if not ok:
            messages.info(request, result)
            return redirect("/")
    return render(request, "profile.html", {'contact': result})


def add_contact(request, passkey):
    if request.method == 'POST':
        form = AddContactForm(request.POST)
        with database.DBSession() as sess:
            ok, result = sess.add_contact(passkey, form['wechat_id'].value())
            # if not ok:
            #     messages.info(request, result)
            return JsonResponse({'msg': result})


def delete_contact(request, passkey, wechat_id):
    with database.DBSession() as sess:
        ok, result = sess.delete_contact(passkey, wechat_id)
        messages.info(request, result)
    return redirect("/contacts/" + passkey)


def update_contact(request, passkey, wechat_id):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        alias = form['alias'].value()
        tag = form['tag'].value()
        mobile = form['mobile'].value()
        description = form['description'].value()
        source = form['source'].value()
        with database.DBSession() as sess:
            ok, result = sess.update_contact(passkey, wechat_id, alias, tag, mobile, description, source)
            return JsonResponse({'msg': result})

            # messages.info(request, result)
    # return redirect("/contacts/%s/%s/" % (passkey, wechat_id))


def update_profile(request, passkey):
    if request.method == 'POST':
        form = ChangeProfileForm(request.POST)
        with database.DBSession() as sess:
            ok, result = sess.update_profile(passkey,
                                             form['name'].value(),
                                             form['gender'].value(),
                                             form['region'].value(),
                                             form['whats_up'].value(),
                                             form['phone'].value(),
                                             form['email'].value())
            return JsonResponse({'msg': result})


def add_oa(request, passkey):
    if request.method == 'POST':
        form = AddOAForm(request.POST)
        with database.DBSession() as sess:
            ok, result = sess.add_oa(passkey, form['oa_name'].value())

            return JsonResponse({'msg': result})


def add_group(request, passkey):
    if request.method == 'POST':
        data = json.loads(request.body)
        with database.DBSession() as sess:
            ok, result = sess.add_group(passkey, data['name'], data['notice'], data['list'])
            return JsonResponse({'msg': result})


def delete_group(request, passkey):
    if request.method == 'POST':
        data = json.loads(request.body)
        with database.DBSession() as sess:
            ok, result = sess.delete_group(passkey, data['name'])
            return JsonResponse({'msg': result})


def admin(request, passkey):
    if passkey is None:
        messages.info(request, NOT_LOGIN_MSG)
        return redirect("/admin_login")

    with database.DBSession() as sess:
        ok, result = sess.admin_get_users(passkey)
        if not ok:
            messages.info(request, result)
            return redirect("/")
    return render(request, "admin.html", {'users': result})


def admin_op(request, passkey):
    if passkey is None:
        messages.info(request, NOT_LOGIN_MSG)
        return redirect("/admin_login")

    if request.method == 'POST':
        data = json.loads(request.body)
        with database.DBSession() as sess:
            ok, result = sess.admin_op(passkey, data['results'])
            return JsonResponse({'msg': result})


def admin_oa(request, passkey):
    if passkey is None:
        messages.info(request, NOT_LOGIN_MSG)
        return redirect("/admin_login")

    if request.method == 'POST':
        data = json.loads(request.body)
        with database.DBSession() as sess:
            ok, result = sess.admin_new_oa(passkey, data['oa_name'], data['oa_desc'])
            return JsonResponse({'msg': result})


def search(request, passkey):
    if passkey is None:
        messages.info(request, NOT_LOGIN_MSG)
        return redirect("/")

    if request.method == 'POST':
        data = json.loads(request.body)
        with database.DBSession() as sess:
            ok, result = sess.search(passkey, data['keyword'])
            return JsonResponse(result)
