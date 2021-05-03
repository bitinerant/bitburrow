import 'package:flutter/material.dart';
import 'dart:async';

import 'package:flutter/services.dart';
import 'package:starflut/starflut.dart';

class Python {
  String _platformVersion = 'Unknown';

  static String format(String fmt,List<Object> params) {
    int matchIndex = 0;
    String replace(Match m) {
      if (matchIndex<params.length) {
        switch (m[4]) {
          case "f":
            num val = params[matchIndex++];
            String str;
            if (m[3]!=null && m[3].startsWith(".")) {
              str = val.toStringAsFixed(int.parse(m[3].substring(1)));
            } else {
              str = val.toString();
            }
            if (m[2]!=null && m[2].startsWith("0")) {
              if (val<0) {
                str = "-"+str.substring(1).padLeft(int.parse(m[2]),"0");
              } else {
                str = str.padLeft(int.parse(m[2]),"0");
              }
            }
            return str;
          case "d":
          case "x":
          case "X":
            int val = params[matchIndex++];
            String str = (m[4]=="d")?val.toString():val.toRadixString(16);
            if (m[2]!=null && m[2].startsWith("0")) {
              if (val<0) {
                str = "-"+str.substring(1).padLeft(int.parse(m[2]),"0");
              } else {
                str = str.padLeft(int.parse(m[2]),"0");
              }
            }
            return (m[4]=="X")?str.toUpperCase():str.toLowerCase();
          case "s":
            return params[matchIndex++].toString();
        }
      } else {
        throw new Exception("Missing parameter for string format");
      }
      throw new Exception("Invalid format string: "+m[0].toString());
    }
  }

  // Platform messages are asynchronous, so we initialize in an async method.
  Run() async {
    String platformVersion;
    // Platform messages may fail, so we use a try/catch PlatformException.
    try {
        String Path1  = await Starflut.getResourcePath();
        String Path2 = await Starflut.getAssetsPath();
        StarCoreFactory starcore = await Starflut.getFactory();
        StarServiceClass Service = await starcore.initSimple("test", "123", 0, 0, []);
        await starcore.regMsgCallBackP(
                (int serviceGroupID, int uMsg, Object wParam, Object lParam) async{
              print("$serviceGroupID  $uMsg   $wParam   $lParam");
              return null;
            });
        StarSrvGroupClass SrvGroup = await Service["_ServiceGroup"];

        /*--macos--*/
        int Platform = await Starflut.getPlatform();
        if( Platform == Starflut.MACOS ) {
          await starcore.setShareLibraryPath(
              Path1); //set path for interface library
          bool LoadResult = await Starflut.loadLibrary(Path1+"/libpython3.9.dylib");
          print("$LoadResult");  //--load
          await Starflut.setEnv("PYTHONPATH","/Library/Frameworks/Python.framework/Versions/3.9/lib/python3.9");
          String pypath = await Starflut.getEnv("PYTHONPATH");
          print("$pypath");
        }else if( Platform == Starflut.WINDOWS ) {
          await starcore.setShareLibraryPath(
              Path1.replaceAll("\\","/")); //set path for interface library
        }

        /*---script python--*/
        bool isAndroid = await Starflut.isAndroid();
        if( isAndroid == true ){
          await Starflut.copyFileFromAssets("testcallback.py", "flutter_assets/python","flutter_assets/python");
          await Starflut.copyFileFromAssets("testpy.py", "flutter_assets/python","flutter_assets/python");
          await Starflut.copyFileFromAssets("python3.9.zip", null,null);  //desRelatePath must be null

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

          await Starflut.copyFileFromAssets("zlib.cpython-39.so", LibraryPath,null);
          await Starflut.copyFileFromAssets("unicodedata.cpython-39.so", LibraryPath,null);
          await Starflut.loadLibrary("libpython3.9.so");
        }

        String docPath = await Starflut.getDocumentPath();
        print("docPath = $docPath");

        String resPath = await Starflut.getResourcePath();
        print("resPath = $resPath");

        String assetsPath = await Starflut.getAssetsPath();
        print("assetsPath = $assetsPath");

        dynamic rr1 = await SrvGroup.initRaw("python39", Service);

        print("initRaw = $rr1");
        var Result = await SrvGroup.loadRawModule("python", "", assetsPath + "/flutter_assets/python/" + "testpy.py", false);
        print("loadRawModule = $Result");

        dynamic python = await Service.importRawContext(null,"python", "", false, "");
        print("python = "+ await python.getString());

        StarObjectClass retobj = await python.call("tt", ["hello ", "world"]);
        print(await retobj[0]);
        print(await retobj[1]);

        print(await python["g1"]);

        StarObjectClass yy = await python.call("yy", ["hello ", "world", 123]);
        print(await yy.call("__len__",[]));

        StarObjectClass multiply = await Service.importRawContext(null,"python", "Multiply", true, "");
        StarObjectClass multiply_inst = await multiply.newObject(["", "", 33, 44]);
        print(await multiply_inst.getString());

        print(await multiply_inst.call("multiply", [11, 22]));

        await SrvGroup.clearService();
        await starcore.moduleExit();

        print("finish");

    } on PlatformException catch (e) {
      print("{$e.message}");
      platformVersion = 'Failed to get platform version.';
    }

  }
}
