import sys

try:
	import unittest
	import phobos

	class TestPhobosAddon(unittest.TestCase):

		def test_addon_enabled(self):
		    # test if addon got loaded correctly
		    # every addon must provide the "bl_info" dict
		    self.assertIsNotNone(phobos.bl_info)

	# we have to manually invoke the test runner here, as we cannot use the CLI
	suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestPhobosAddon)
	unittest.TextTestRunner().run(suite)
except:
	sys.exit(1)
