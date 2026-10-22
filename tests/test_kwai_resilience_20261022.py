import os,sys,unittest
from pathlib import Path
from unittest.mock import patch
import xml.etree.ElementTree as ET

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
import kwai_physical_queue_daemon as daemon
import kwai_native_cortes as native
import kwai_device_failover_worker as worker
from android_device_adapters import ensure_memu_transport

class R:
 def __init__(self, stdout='',rc=0):
  self.stdout=stdout;self.stderr='';self.returncode=rc

class KwaiRecoveryRegressions(unittest.TestCase):
 def test_physical_port_autodiscovery_survives_other_server_claiming_usb(self):
  calls=[]
  def fake(args, **kwargs):
   calls.append(args)
   port=args[args.index('-P')+1]
   if port=='5038':return R('List of devices attached\n127.0.0.1:21543 offline\n')
   return R('List of devices attached\n993fce720408 device product:galahad model:M2004J19C\n')
  old=dict(daemon._PORT_CACHE)
  try:
   daemon._PORT_CACHE.update(until=0)
   with patch.object(daemon.subprocess,'run',side_effect=fake):
    self.assertEqual(daemon.physical_adb_port(),'5037')
   self.assertEqual([x[2] for x in calls],['5038','5037'])
  finally:daemon._PORT_CACHE.update(old)

 def test_editor_screen_is_preserved_without_tapping_publish(self):
  root=ET.Element('hierarchy')
  ET.SubElement(root,'node',{'resource-id':'kwai.lite.video.product:id/edit_post_next_step_button'})
  with patch.object(native,'dump',return_value=(root,'ui.xml')),patch.object(native,'tap') as tap:
   with self.assertRaisesRegex(native.E,'editor-screen-active:preserve-draft'):
    native.wait('DUMMY',native.RID_PROFILE,'unit',seconds=2)
   tap.assert_not_called()

 def test_editor_error_is_eligible_for_safe_precommit_failover(self):
  self.assertEqual(worker.classify_failure('KWAI_UP_STATE=FAILED ERROR=ui-surface-unexpected:editor-screen-active:preserve-draft',79),'device')

 def test_phone_adapter_obeys_discovered_port(self):
  from android_device_adapters import PhysicalDeviceAdapter
  calls=[]
  def fake(args,**kwargs):
   calls.append(args)
   if args[-1]=='get-state':return R('device\n')
   if args[-2:]==['getprop','sys.boot_completed']:return R('1\n')
   if 'pm' in args and 'path' in args:return R('package:/data/app/kwai.lite.video/base.apk\n')
   return R('')
  with patch.dict(os.environ,{'ANTHARES_PHYSICAL_ADB_PORT':'5037','ANTHARES_PHYSICAL_KWAI_AUTHENTICATED':'true'}):
   status=PhysicalDeviceAdapter('PHONE',run=fake).probe()
  self.assertTrue(status.ready)
  self.assertTrue(all(x[2]=='5037' for x in calls))
 def test_memu_transport_uses_isolated_5037_socket(self):
  calls=[]
  def fake(args,**kwargs):
   calls.append((args,kwargs))
   return R('device\n' if args[-1]=='get-state' else 'connected\n')
  with patch.dict(os.environ,{'ADB_SERVER_SOCKET':'tcp:127.0.0.1:5038'}):
   self.assertTrue(ensure_memu_transport('adb','127.0.0.1:21543',run=fake))
  self.assertTrue(calls)
  for args,kwargs in calls:
   self.assertIn('5037',args)
   self.assertEqual(kwargs['env']['ADB_SERVER_SOCKET'],'tcp:127.0.0.1:5037')

if __name__=='__main__':unittest.main()
