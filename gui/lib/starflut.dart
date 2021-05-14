import 'dart:async';
import 'package:starflut/starflut.dart';

class Python {
  static final Python _instance = Python.init(); // singleton
  StarCoreFactory starcore = null;
  StarServiceClass Service = null;
  StarSrvGroupClass SrvGroup = null;
  Python.init();

  static Future<Python> create() async {
    await _instance._init();
    return _instance;
  }

  Future _init() async {
    String Path1 = await Starflut.getResourcePath();
    // String Path2 = await Starflut.getAssetsPath();
    starcore = await Starflut.getFactory();
    Service = await starcore.initSimple("test", "123", 0, 0, []);
    // await starcore.regMsgCallBackP(
    //         (int serviceGroupID, int uMsg, Object wParam, Object lParam) async{
    //       print("$serviceGroupID  $uMsg   $wParam   $lParam");
    //       return null;
    //     });
    SrvGroup = await Service["_ServiceGroup"];
    int Platform = await Starflut.getPlatform();
    if( Platform == Starflut.MACOS ) {
      await starcore.setShareLibraryPath(
          Path1); //set path for interface library
      bool LoadResult = await Starflut.loadLibrary(Path1+"/libpython3.9.dylib");
      print("$LoadResult");  //--load
      await Starflut.setEnv("PYTHONPATH","/Library/Frameworks/Python.framework/Versions/3.9/lib/python3.9");
      String pypath = await Starflut.getEnv("PYTHONPATH");
      print("$pypath");
    } else if( Platform == Starflut.WINDOWS ) {
      await starcore.setShareLibraryPath(
          Path1.replaceAll("\\","/")); //set path for interface library
    }
    bool isAndroid = await Starflut.isAndroid();
    if( isAndroid == true ){
      // await Starflut.copyFileFromAssets("testcallback.py", "flutter_assets/python","flutter_assets/python");
      await Starflut.copyFileFromAssets("testpy.py", "flutter_assets/python","flutter_assets/python");  // FIXME: copyFileFromAssets() only needed at install time
      await Starflut.copyFileFromAssets("python3.9.zip", null, null);  // desRelatePath must be null
      var nativepath = await Starflut.getNativeLibraryDir();
      var LibraryPath = "";
      if( nativepath.contains("x86_64"))
        LibraryPath = "x86_64";
      else if( nativepath.contains("arm64"))
        LibraryPath = "arm64-v8a";
      else if( nativepath.contains("arm"))
        LibraryPath = "armeabi";
      else if( nativepath.contains("x86"))
        LibraryPath = "x86";
      // copy Python C modules; see also ../android/app/src/main/build.sh
      // ... and https://uonfu.com/q/srplab/starcore_for_flutter/5/776902757
      await Starflut.copyFileFromAssets("zlib.cpython-39.so", LibraryPath,null);
      await Starflut.copyFileFromAssets("unicodedata.cpython-39.so", LibraryPath,null);
      await Starflut.copyFileFromAssetsEx("_socket.cpython-39.so", LibraryPath, null, false);
      await Starflut.copyFileFromAssetsEx("math.cpython-39.so", LibraryPath, null, false);
      await Starflut.copyFileFromAssetsEx("select.cpython-39.so", LibraryPath, null, false);
      await Starflut.copyFileFromAssetsEx("array.cpython-39.so", LibraryPath, null, false);
      await Starflut.copyFileFromAssetsEx("_hashlib.cpython-39.so", LibraryPath, null, false);
      await Starflut.copyFileFromAssetsEx("_struct.cpython-39.so", LibraryPath, null, false);
      await Starflut.copyFileFromAssetsEx("binascii.cpython-39.so", LibraryPath, null, false);
      await Starflut.copyFileFromAssetsEx("_blake2.cpython-39.so", LibraryPath, null, false);
      await Starflut.copyFileFromAssetsEx("_contextvars.cpython-39.so", LibraryPath, null, false);
      await Starflut.copyFileFromAssetsEx("_random.cpython-39.so", LibraryPath, null, false);
      await Starflut.copyFileFromAssetsEx("_posixsubprocess.cpython-39.so", LibraryPath, null, false);
      await Starflut.copyFileFromAssetsEx("_csv.cpython-39.so", LibraryPath, null, false);
      await Starflut.loadLibrary("libpython3.9.so");
    }
    // String docPath = await Starflut.getDocumentPath();
    // print("docPath = $docPath");
    // String resPath = await Starflut.getResourcePath();
    // print("resPath = $resPath");
    String assetsPath = await Starflut.getAssetsPath();
    // print("assetsPath = $assetsPath");
    dynamic rr1 = await SrvGroup.initRaw("python39", Service);
    // print("initRaw = $rr1");
    var Result = await SrvGroup.loadRawModule("python", "", assetsPath + "/flutter_assets/python/" + "testpy.py", false);
    // print("loadRawModule = $Result");
    // dynamic python = await Service.importRawContext(null,"python", "", false, "");
    // print("python = "+ await python.getString());
    // StarObjectClass retobj = await python.call("tt", ["hello ", "world"]);
    // print(await retobj[0]);
    // print(await retobj[1]);
    // print(await python["g1"]);
    // StarObjectClass yy = await python.call("yy", ["hello ", "world", 123]);
    // print(await yy.call("__len__",[]));
    // StarObjectClass multiply = await Service.importRawContext(null,"python", "Multiply", true, "");
    // StarObjectClass multiply_inst = await multiply.newObject(["", "", 33, 44]);
    // print(await multiply_inst.getString());
    // print(await multiply_inst.call("multiply", [11, 22]));
  }

  @override
  void dispose() async {
    await SrvGroup.clearService();
    await starcore.moduleExit();
  }

  Future<String> multiply(int a, int b) async {
    StarObjectClass multiply = await Service.importRawContext(null,"python", "Multiply", true, "");
    StarObjectClass multiply_inst = await multiply.newObject(["", "", 33, 44]);
    return await multiply_inst.call("multiply", [a, b]);
  }
}
