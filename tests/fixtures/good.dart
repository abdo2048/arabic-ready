Widget build(BuildContext context) {
  return Padding(
    padding: const EdgeInsetsDirectional.only(start: 16, end: 8),
    child: Align(
      alignment: AlignmentDirectional.centerStart,
      child: Text('مرحبا', textAlign: TextAlign.start),
    ),
  );
}
final p = EdgeInsetsDirectional.fromSTEB(16, 0, 8, 0);
final s = Stack(children: [PositionedDirectional(start: 0, child: Icon(Icons.arrow_back))]);
final c = EdgeInsets.symmetric(horizontal: 16);
