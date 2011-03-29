# Layers setting up fixtures with a CMFDefault site.

import contextlib

from plone.testing import Layer
from plone.testing import zodb, zca, z2

SITE_ID = 'portal'
SITE_TITLE = u"CMFDefault site"

TEST_USER_ID = 'test_user_1_'
TEST_USER_PASSWORD = 'secret'
TEST_USER_ROLES = ['Member', ]

SITE_OWNER_NAME = 'admin'
SITE_OWNER_PASSWORD = 'secret'


class PortalFixture(Layer):
    """This layer sets up a basic CMFDefault site, with:

    * No content
    * No default workflow
    * One user, as found in the constant ``TEST_USER_ID``, with login name
      ``TEST_USER_NAME``, the password ``TEST_USER_PASSWORD``, and a single
      role, ``Member``.
    """

    defaultBases = (z2.STARTUP,)

    # Products that will be installed, plus options
    products = (
            ('Products.GenericSetup', {'loadZCML': True},),
            ('Products.DCWorkflow', {'loadZCML': True}, ),
            ('Products.ZCTextIndex', {'loadZCML': True}, ),

            ('Products.CMFActionIcons', {'loadZCML': True}, ),
            ('Products.CMFUid', {'loadZCML': True}, ),
            ('Products.CMFCalendar', {'loadZCML': True}, ),

            ('Products.CMFCore', {'loadZCML': True},),
            ('Products.CMFDefault', {'loadZCML': True}, ),
            ('Products.MailHost', {'loadZCML': True}, ),

        )

    # Layer lifecycle

    def setUp(self):

        # Stack a new DemoStorage on top of the one from z2.STARTUP.
        self['zodbDB'] = zodb.stackDemoStorage(self.get('zodbDB'),
            name='CMFPortalFixture')

        self.setUpZCML()

        # Set up products and the default content
        with z2.zopeApp() as app:
            self.setUpProducts(app)
            self.setUpDefaultContent(app)

    def tearDown(self):

        # Tear down products
        with z2.zopeApp() as app:
            # note: content tear-down happens by squashing the ZODB
            self.tearDownProducts(app)

        self.tearDownZCML()

        # Zap the stacked ZODB
        self['zodbDB'].close()
        del self['zodbDB']

    def setUpZCML(self):
        """Stack a new global registry and load ZCML configuration of
        CMFDefault and the core set of add-on products into it.
        """

        # Create a new global registry
        zca.pushGlobalRegistry()

        from zope.configuration import xmlconfig
        self['configurationContext'] = context = zca.stackConfigurationContext(
            self.get('configurationContext'))

        # Load dependent products's ZCML
        # CMFDefault doesn't specify dependencies on Products.* packages fully
        from zope.dottedname.resolve import resolve

        def loadAll(filename):
            for p, config in self.products:
                if not config['loadZCML']:
                    continue
                try:
                    package = resolve(p)
                except ImportError:
                    continue
                try:
                    xmlconfig.file(filename, package, context=context)
                except IOError:
                    pass

        loadAll('meta.zcml')
        loadAll('configure.zcml')
        loadAll('overrides.zcml')

    def tearDownZCML(self):
        """Pop the global component registry stack, effectively unregistering
        all global components registered during layer setup.
        """
        # Pop the global registry
        zca.popGlobalRegistry()

        # Zap the stacked configuration context
        del self['configurationContext']

    def setUpProducts(self, app):
        """Install all old-style products listed in the the ``products`` tuple
        of this class.
        """

        for p, config in self.products:
            z2.installProduct(app, p)

    def tearDownProducts(self, app):
        """Uninstall all old-style products listed in the the ``products``
        tuple of this class.
        """
        for p, config in reversed(self.products):
            z2.uninstallProduct(app, p)

        # Clean up Wicked turds
        # XXX: This may tear down too much state
        try:
            from wicked.fieldevent import meta
            meta.cleanUp()
        except ImportError:
            pass

    def setUpDefaultContent(self, app):
        """Add the site owner user to the root user folder and log in as that
        user. Create the CMFDefault site, installing the extension profiles
        listed in the ``extensionProfiles`` layer class variable. Create the
        test user inside the site.

        Note: There is no explicit tear-down of this setup operation, because
        all persistent changes are torn down when the stacked ZODB
        ``DemoStorage`` is popped.
        """

        # Create the owner user and "log in" so that the site object gets
        # the right ownership information
        app['acl_users'].userFolderAddUser(
                SITE_OWNER_NAME,
                SITE_OWNER_PASSWORD,
                ['Manager'],
                []
            )

        z2.login(app['acl_users'], SITE_OWNER_NAME)

        # Create the site with the default set of extension profiles
        from Products.CMFDefault.factory import addConfiguredSite
        addConfiguredSite(app, SITE_ID,
            "Products.CMFDefault:default")

        # Create the test user.
        app[SITE_ID]['acl_users'].userFolderAddUser(
                TEST_USER_ID,
                TEST_USER_PASSWORD,
                TEST_USER_ROLES,
                []
                )

        # Log out again
        z2.logout()

# CMFDefault fixture layer instance. Should not be used on its own, but as a
# base for other layers.

PORTAL_FIXTURE = PortalFixture(name='PORTAL_FIXTURE')


class CMFDefaultTestLifecycle(object):
    """Mixin class for CMFDefault test lifecycle. This exposes the ``portal``
    resource and resets the environment between each test.

    This class is used as a mixing for the IntegrationTesting and
    FunctionalTesting classes below, which also mix in the z2 versions of
    the same.
    """

    defaultBases = (PORTAL_FIXTURE,)

    def testSetUp(self):
        super(CMFDefaultTestLifecycle, self).testSetUp()

        self['portal'] = portal = self['app'][SITE_ID]
        self.setUpEnvironment(portal)

    def testTearDown(self):
        self.tearDownEnvironment(self['portal'])
        del self['portal']

        super(CMFDefaultTestLifecycle, self).testTearDown()

    def setUpEnvironment(self, portal):
        """Set up the local component site, reset skin data and log in as
        the test user.
        """

        # Set up the local site manager
        from zope.site.hooks import setSite
        setSite(portal)

        # Reset skin data
        portal.clearCurrentSkin()
        portal.setupCurrentSkin(portal.REQUEST)

        # Pseudo-login as the test user
        z2.login(portal['acl_users'], TEST_USER_ID)

    def tearDownEnvironment(self, portal):
        """Log out, invalidate standard RAM caches, and unset the local
        component site to clean up after tests.
        """

        # Clear the security manager
        z2.logout()

        # Unset the local component site
        from zope.site.hooks import setSite
        setSite(None)


class IntegrationTesting(CMFDefaultTestLifecycle, z2.IntegrationTesting):
    """CMFDefault version of the integration testing layer
    """


class FunctionalTesting(CMFDefaultTestLifecycle, z2.FunctionalTesting):
    """CMFDefault version of the functional testing layer
    """

#
# Layer instances
#

# Note: PORTAL_FIXTURE is defined above

PORTAL_INTEGRATION_TESTING = IntegrationTesting(bases=(PORTAL_FIXTURE,),
    name='PORTAL_INTEGRATION_TESTING')
PORTAL_FUNCTIONAL_TESTING = FunctionalTesting(bases=(PORTAL_FIXTURE,),
    name='PORTAL_FUNCTIONAL_TESTING')

PORTAL_ZSERVER = FunctionalTesting(bases=(PORTAL_FIXTURE, z2.ZSERVER_FIXTURE),
    name='PORTAL_ZSERVER')
PORTAL_FTP_SERVER = FunctionalTesting(
    bases=(PORTAL_FIXTURE, z2.FTP_SERVER_FIXTURE),
    name='PORTAL_FTP_SERVER')


@contextlib.contextmanager
def CMFDefaultPortal(db=None, connection=None, environ=None):
    """Context manager for working with the Plone portal during layer setup::

        with CMFDefaultPortal() as portal:
            ...

    This is based on the ``z2.zopeApp()`` context manager. See the module
     ``plone.testing.z2`` for details.

    Do not use this in a test. Use the 'portal' resource from the PloneFixture
    layer instead!

    Pass a ZODB handle as ``db`` to use a specificdatabase. Alternatively,
    pass an open connection as ``connection`` (the connection will not be
    closed).
    """

    from zope.site.hooks import setSite, getSite, setHooks
    setHooks()

    site = getSite()

    with z2.zopeApp(db, connection, environ) as app:
        portal = app[SITE_ID]

        setSite(portal)
        z2.login(portal['acl_users'], TEST_USER_ID)

        try:
            yield portal
        finally:
            z2.logout()
            if site is not portal:
                setSite(site)


def applyProfile(portal, profileName):
    """Install an extension profile into the portal. The profile name
    should be a package name and a profile name, e.g. 'my.product:default'.
    """

    from Acquisition import aq_parent
    from AccessControl import getSecurityManager
    from AccessControl.SecurityManagement import setSecurityManager

    sm = getSecurityManager()
    app = aq_parent(portal)

    z2.login(app['acl_users'], SITE_OWNER_NAME)

    try:
        setupTool = portal['portal_setup']
        profileId = 'profile-%s' % (profileName,)
        setupTool.runAllImportStepsFromProfile(profileId)

        portal.clearCurrentSkin()
        portal.setupCurrentSkin(portal.REQUEST)

    finally:
        setSecurityManager(sm)
