Widget build(BuildContext context) {
  return Padding(
    padding: const EdgeInsets.only(left: 16, right: 8),
    child: Align(
      alignment: Alignment.centerLeft,
      child: Text('مرحبا', textAlign: TextAlign.left),
    ),
  );
}
final p = EdgeInsets.fromLTRB(16, 0, 8, 0);
final s = Stack(children: [Positioned(left: 0, child: Icon(Icons.arrow_back))]);
