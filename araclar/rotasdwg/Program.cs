// ROTAŞ: DXF -> DWG (ACadSharp). Kullanım: rotasdwg giris.dxf cikis.dwg [AC1032|AC1027|AC1018]
using ACadSharp;
using ACadSharp.IO;

var inp = args[0]; var outp = args[1];
var ver = args.Length > 2 ? args[2] : "AC1032";
CadDocument doc;
using (var r = new DxfReader(inp)) { doc = r.Read(); }
string first<T>(IEnumerable<T> xs, Func<T,string> f, string want) { var l = xs.Select(f).ToList(); return l.Contains(want) ? want : (l.Count > 0 ? l[0] : want); }
doc.Header.CurrentDimensionStyleName = first(doc.DimensionStyles, x => x.Name, "Standard");
doc.Header.CurrentTextStyleName = first(doc.TextStyles, x => x.Name, "Standard");
doc.Header.DimensionTextStyleName = first(doc.TextStyles, x => x.Name, "Standard");
doc.Header.CurrentLayerName = first(doc.Layers, x => x.Name, "0");
doc.Header.CurrentLineTypeName = first(doc.LineTypes, x => x.Name, "ByLayer");
doc.Header.Version = ver switch { "AC1027" => ACadVersion.AC1027, "AC1018" => ACadVersion.AC1018, "AC1024" => ACadVersion.AC1024, _ => ACadVersion.AC1032 };
using (var w = new DwgWriter(outp, doc)) { w.Write(); }
// geri okuma kontrolü
CadDocument back;
using (var rr = new DwgReader(outp)) { back = rr.Read(); }
Console.WriteLine($"varlık: dxf={doc.Entities.Count()} dwg={back.Entities.Count()} katman={back.Layers.Count()} blok={back.BlockRecords.Count()}");
