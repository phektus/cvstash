from datetime import datetime
import random
import string
from gluon.contrib.pyfpdf import FPDF, HTMLMixin

def __getUserSettings(user):
    """
    Initiate and/or return user settings
    """
    settings = db(db.usersettings.owner==user.id).select().first()
    if not settings:
        # create user settings
        first_name = user.first_name.lower()
        last_name = user.last_name.lower()
        seed = ''.join(random.choice(string.letters+'1234567890') for i in xrange(9))
        resumeurl = '%s_%s_%s' % (first_name, last_name, seed)
        resumeurl = resumeurl.replace('  ',' ')
        resumeurl = resumeurl.replace('  ',' ')
        resumeurl = resumeurl.replace(' ','_')
        settings = db.usersettings.insert(owner=user.id, activetemplate=DEFAULT_TEMPLATE, resumeurl=resumeurl)

    return settings

def __getUserProfile(user):
    """
    Return a tuple containing profile information and update form
    """
    userprofile = db(db.userprofile.owner==user.id).select().first()\
        or db.userprofile.insert(first_name=user.first_name, last_name=user.last_name)
    return userprofile

def __getContactInfo(user):
    """
    Return a tuple containing contact information and update form
    """
    contactinfo = db(db.contactinfo.owner==user.id).select().first()\
        or db.contactinfo.insert(email=user.email)
    return contactinfo

def user():
    "login, registration, etc."
    searchstring = session.searchstring or ''
    rpx = ''
    registerurl=URL('default', 'user', args='register')
    if request.vars.token:
        auth.settings.login_form = rpxform
        form = auth()
        return locals()

    if 'login' in request.args:
        rpx = rpxform.login_form()
        html = DIV(
                DIV(
                  H2(A('Click here to register',_href=registerurl), _id='extra_register'),
                  H3('Or login if you already have an account'),
                  auth(),
                  SPAN(A('Forgot My Password',_href=URL(r=request, args='request_reset_password'))),
                  _id='login_auth'),
                DIV(
                  BR(),
                  H3('You can also make use of existing identities'),
                  rpx,
                  _id='login_rpx'),

               )
    else:
        html = DIV(auth(), _id='user_form')

    form = html

    latest_users = []

    return locals()

def download():
    "to download images"
    return response.download(request, db)

def call():
    "for services"
    session.forget()
    return service()

def index():
    "welcome page"
    latest_users = db(db.landing_page_users.id>0).select()
    stats = db(db.landing_page_stats.id>0).select().first()

    if auth.user_id:
        redirect(URL('dashboard'))
    searchstring = session.searchstring or ''
    return locals()

def cv():
    "handler for shortened url calls"
    if request.args(0) is None:
        redirect(URL('public/'))
    usersettings = db(db.usersettings.resumeurl==request.args(0)).select().first()
    if usersettings is None:
        redirect(URL('public/'))
    user = db(db.auth_user.id==usersettings.owner).select().first()
    redirect(URL('public/'+str(user.id)))


def public():
    "view the cv public"
    now = datetime.now()
    entries = None
    contactinfo = None
    userprofile = None
    usersettings = None
    activetemplate = DEFAULT_TEMPLATE
    user = db.auth_user(request.args(0) or auth.user_id)

    if user:
        # profile
        userprofile = __getUserProfile(user)
        try:
            mycountry = [country['name'] for country in countries if country['code']==userprofile.country][0]
        except:
            mycountry = None

        # skills
        skills = db(db.skill.owner==user.id).select(orderby=~db.skill.name,limitby=(0,MAX_SKILLS))

        # resume entries
        entries = db(db.entry.owner==user.id).select(orderby=~db.entry.start,limitby=(0,MAX_ENTRIES))

        # contact information
        contactinfo = __getContactInfo(user)

        # direct link
        usersettings = __getUserSettings(user)
        activetemplate = usersettings.activetemplate

        # entries by type
        work_entries = db((db.entry.owner==user.id)&(db.entry.type=='work')).select(orderby=~db.entry.start)
        education_entries = db((db.entry.owner==user.id)&(db.entry.type=='education')).select(orderby=~db.entry.start)
        personal_entries = db((db.entry.owner==user.id)&(db.entry.type=='personal')).select(orderby=~db.entry.start)

        response.title = "%s %s | Free Resume Builder | CVStash" % (userprofile.first_name, userprofile.last_name)

    else:
        redirect(URL('index/'))

    return locals()

@auth.requires_login()
def dashboard():
    """
    Main control interface
    """
    now = datetime.now()
    entries = None
    skills = None
    contactinfo = None
    userprofile = None
    resumeurl = None
    scrollto = 'userprofile'
    user = db.auth_user(auth.user_id)

    if user is not None:
        # new entry form
        new_entryform = SQLFORM(db.entry, submit_button='Add Entry', showid=False)
        if new_entryform.accepts(request.vars, session):
            scrollto = 'entries'
            if db(db.entry.owner==auth.user.id).count()>MAX_ENTRIES:
                db.rollback()
                response.flash = 'ERROR: max(%d) entries reached' % MAX_ENTRIES
            else:
                response.flash = 'Entry successfully added'
        elif new_entryform.errors:
            scrollto = 'addentry'
            if new_entryform.errors.get('operation'):
                response.flash = new_entryform.errors.get('operation')
            else:
                response.flash = 'Errors found when adding entry'

        # individual entries and forms
        entries = db(db.entry.owner==user.id).select(orderby=~db.entry.start,limitby=(0,MAX_ENTRIES))
        entry_change = False
        entry_forms = []
        for entry_obj in entries:
            entry_form = SQLFORM(db.entry, entry_obj, deletable=True, submit_button='Update Entry', showid=False)
            entry_forms.append({'form': entry_form, 'entry': entry_obj})
            if entry_form.accepts(request.vars, session):
                entry_change = True
                if request.vars.delete_this_record == 'on':
                    scrollto = 'entries'
                    response.flash = "Entry '%s' deleted" % entry_obj.title
                else:
                    scrollto = 'entryform_%d' % entry_obj.id
                    response.flash = "Entry '%s' updated" % entry_obj.title
            elif entry_form.errors:
                scrollto = 'entryform_%d' % entry_obj.id
                response.flash = "Errors found while editing entry '%s'" % entry_obj.title
        if entry_change:
            # fetch again to reflect changes
            entries = db(db.entry.owner==user.id).select(orderby=~db.entry.start,limitby=(0,MAX_ENTRIES))

        # skills
        new_skillform = SQLFORM(db.skill, submit_button='Add Skill', showid=False)
        if new_skillform.accepts(request.vars, session):
            scrollto = 'skills'
            if db(db.skill.owner==auth.user.id).count()>MAX_SKILLS:
                db.rollback()
                response.flash = 'ERROR: max(%d) skills reached' % MAX_SKILLS
            else:
                response.flash = 'Skill successfully added'
        elif new_skillform.errors:
            scrollto = 'addskill'
            if new_skillform.errors.get('operation'):
                response.flash = new_skillform.errors.get('operation')
            else:
                response.flash = 'Errors found when adding skill'
        skills = db(db.skill.owner==user.id).select(orderby=~db.skill.name,limitby=(0,MAX_SKILLS))
        skill_change = False
        skill_forms = []
        for skill_obj in skills:
            skill_form = SQLFORM(db.skill, skill_obj, deletable=True, submit_button='Update Skill', showid=False)
            skill_forms.append({'form': skill_form, 'skill': skill_obj})
            if skill_form.accepts(request.vars, session):
                scrollto = 'skills'
                skill_change = True
                if request.vars.delete_this_record == 'on':
                    response.flash = "Skill '%s' deleted" % request.vars.name
                else:
                    response.flash = "Skill '%s' updated" % request.vars.name
            elif skill_form.errors:
                scrollto = 'skills'
                response.flash = "Errors found while editing skill '%s'" % skill_obj.name
        if skill_change:
            # fetch again to reflect changes
            skills = db(db.skill.owner==user.id).select(orderby=~db.skill.name,limitby=(0,10))

        # contact info form
        contactinfo = __getContactInfo(user)
        contactform = SQLFORM(db.contactinfo, contactinfo, submit_button='Update Contact Info')
        if contactform.accepts(request.vars, session):
           scrollto = 'contact_info'
           response.flash = 'Contact info updated'
        elif contactform.errors:
           scrollto = 'contact_info'
           response.flash = 'Errors found in contact info'

        # user profile form
        userprofile = __getUserProfile(user)
        userprofileform = SQLFORM(db.userprofile, userprofile, submit_button='Update Profile')
        if userprofileform.accepts(request.vars, session):
           response.flash = 'Profile updated'
        elif userprofileform.errors:
           response.flash = 'Errors found in profile'
        if not userprofile.created:
            userprofile.update_record(created=now)

        # load the user settings
        usersettings = __getUserSettings(user)

    return locals()

def pdfdownload():
    "view the cv as pdf"

    if request.args(0) is None:
        redirect(URL('public/'))
    user = db.auth_user(request.args(0) or auth.user_id)

    now = datetime.now()
    entries = None
    contactinfo = None
    userprofile = None

    if user:
        usersettings = __getUserSettings(user)
        # profile
        userprofile = __getUserProfile(user)
        try:
            mycountry = [country['name'] for country in countries if country['code']==userprofile.country][0]
        except:
            mycountry = None

        # resume entries
        entries = db(db.entry.owner==user.id).select(orderby=~db.entry.start,limitby=(0,10))

        # contact information
        contactinfo = __getContactInfo(user)

        # direct link
        resumeurl = usersettings.resumeurl or ''

        # entries by type
        work_entries = db((db.entry.owner==user.id)&(db.entry.type=='work')).select(orderby=~db.entry.start)
        education_entries = db((db.entry.owner==user.id)&(db.entry.type=='education')).select(orderby=~db.entry.start)
        personal_entries = db((db.entry.owner==user.id)&(db.entry.type=='personal')).select(orderby=~db.entry.start)

        response.title = "%s %s Resume (PDF) | cvstash.com" % (userprofile.first_name, userprofile.last_name)
    return locals()

@auth.requires_login()
def success():
    user = db.auth_user(auth.user_id)
    userprofile = __getUserProfile(user)
    return locals()

def search():
    results = []
    google_url = ''
    if request.vars.keywords:
        keywords = [x for x in request.vars.keywords.split()]
        searchstring = '+'.join(keywords) + '+site:www.cvstash.com'
        google_url = "http://www.google.com.ph/search?q=%s" % searchstring
        session.searchstring = ' '.join(keywords)
    if google_url is '':
        redirect(URL(r=request, f='index'))
    else:
        redirect(google_url)
