Exception in thread Thread-209 (startBatchConvert):
Traceback (most recent call last):
  File "C:\Program Files\Blender Foundation\Blender 3.1\3.1\python\lib\threading.py", line 1009, in _bootstrap_inner
    self.run()
  File "C:\Program Files\Blender Foundation\Blender 3.1\3.1\python\lib\threading.py", line 946, in run
    self._target(*self._args, **self._kwargs)
  File "C:\Users\User\AppData\Roaming\Blender Foundation\Blender\3.1\scripts\addons\blender-addon-for-trackmania-and-maniaplanet-master\TM_Items_Convert.py", line 375, in startBatchConvert
    tm_props_convertingItems[ current_item_index ].name             = name
AttributeError: Writing to ID classes in this context is not allowed: Scene, Scene datablock, error setting TM_Properties_ConvertingItems.name