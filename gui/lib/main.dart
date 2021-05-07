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
  int _counter = 0;

  static Future<Python> initPython() async {
    return await Python.create();
  }

  void _incrementCounter() {
    setState(() {
      _counter++;
    });
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
    return Scaffold(
      appBar: AppBar(
        brightness: Brightness.dark,  // white notification icons; see https://stackoverflow.com/questions/52489458
        backgroundColor: Colors.brown[600],  // defaults to primarySwatch
        title: FutureBuilder<Python>(
          future: p,
          builder: (context, snapshot) {
            if (snapshot.hasData) {
              return FutureBuilder<String>(
                future: snapshot.data/*!*/.multiply(37, 8),
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
      ),
      body: Container(
        child: _buildHomeList(),
        color: Colors.brown[200],
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: _incrementCounter,
        tooltip: 'Increment',
        child: Icon(Icons.add),
      ),
    );
  }
}
