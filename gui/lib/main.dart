import 'package:flutter/material.dart';
import 'starflut.dart';

void main() {
  runApp(MyApp());
}

class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'BitBurrow',
      theme: ThemeData(
        primarySwatch: Colors.brown,
        accentColor: Colors.amber,
      ),
      home: MyHomePage(title: 'BitBurrow'),
    );
  }
}

class MyHomePage extends StatefulWidget {
  MyHomePage({Key key, this.title}) : super(key: key);

  final String title;

  @override
  _MyHomePageState createState() => _MyHomePageState();
}

class _MyHomePageState extends State<MyHomePage> {
  Future<Python> p = initPython();
  static const List<Tab> tabs = <Tab>[
    Tab(text: 'ROUTERS'),
    Tab(text: 'SERVICES'),
    Tab(text: 'SETTINGS'),
  ];

  static Future<Python> initPython() async {
    return await Python.create();
  }


  Widget _buildHomeList() => ListView.builder(
        // TODO: allow user to change order, maybe via https://pub.dev/packages/drag_and_drop_lists
        itemBuilder: (context, index) {
          if (index < 4) {
            return Card(
                child:
                    Column(mainAxisSize: MainAxisSize.min, children: <Widget>[
              ListTile(
                // formerly: const ListTile(
                // leading: Icon(Icons.wifi),
                leading: index % 2 == 0
                    ? Padding(
                        padding: const EdgeInsets.symmetric(vertical: 12.0),
                        child: Image.asset('images/generic-router.png'),
                      )
                    : Padding(
                        padding: const EdgeInsets.only(left: 10.0),
                        child: Text(
                          '⇐🔒⇒',
                          style: TextStyle(
                            fontWeight: FontWeight.bold,
                            letterSpacing: -5.0,
                          ),
                          textAlign: TextAlign.right,
                        ),
                      ),
                minLeadingWidth: 45.0, // left-align titles
                title: Text('Sue\'s router'),
                subtitle: Text('192.168.' + (index + 121).toString() + '.1'),
              )
            ]));
          } else {
            return null;
          }
        },
      );

  @override
  Widget build(BuildContext context) {
    return DefaultTabController(
      length: tabs.length,
      child: Builder(builder: (BuildContext context) {
        final TabController tabController = DefaultTabController.of(context)/*!*/;
        return Scaffold(
          appBar: AppBar(
            brightness: Brightness.dark,  // white notification icons; see https://stackoverflow.com/questions/52489458
            backgroundColor: Colors.brown[600],  // defaults to primarySwatch
            title: FutureBuilder<Python>(
              future: p,
              builder: (context, snapshot) {
                if (snapshot.hasData) {
                  return FutureBuilder<String>(
                    future: snapshot.data/*!*/.getTestfContents(),
                    builder: (context, snapshot) {
                        if (snapshot.hasData) {
                        return Text("${widget.title}: ${snapshot.data}");
                        } else if (snapshot.hasError) {
                        final error = snapshot.error.toString();
                        print("Error FSAN: $error");
                        return Text("$error");
                        } else {
                        return Text("${widget.title}: loading ...");
                        }
                    }
                  );
                } else if (snapshot.hasError) {
                  final error = snapshot.error.toString();
                  print("Error RANW: $error");
                  return Text("$error");
                } else {
                  return Text("${widget.title}: loading ..");
                }
              }
            ),
            bottom: const TabBar(
              tabs: tabs,
            ),
          ),
          body: TabBarView(
            children: tabs.map((Tab tab) {
              if (tab.text == 'ROUTERS') {
                return Container(
                  child: _buildHomeList(),
                  color: Colors.brown[200],
                );
              } else {
                return Center(
                  child: Text(
                    tab.text/*!*/ + ' Tab',
                    style: Theme.of(context).textTheme.headline5,
                  ),
                );
              }
            }).toList(),
          ),
          floatingActionButton: FloatingActionButton(
           // onPressed: _incrementCounter,
            tooltip: 'Increment',
            child: Icon(Icons.add),
          ),
        );
      }),
    );
  }
}
