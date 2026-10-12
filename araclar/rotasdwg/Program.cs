// ROTAŞ: DXF -> DWG (ACadSharp). Kullanım: rotasdwg giris.dxf cikis.dwg [AC1032|AC1027|AC1018]
using ACadSharp;
using ACadSharp.IO;

var inp = args[0]; var outp = args[1];
var ver = args.Length > 2 ? args[2] : "AC1032";
CadDocument doc;
using (var r = new DxfReader(inp)) { doc = r.Read(); }
string first<T>(IEnumerable<T> xs, Func<T,string> f, string want) { var l = xs.Select(f).ToList(); return l.Contains(want) ? want : (l.Count > 0 ? l[0] : want); }
if (doc.DimensionStyles.Count() > 0) doc.Header.CurrentDimensionStyleName = first(doc.DimensionStyles, x => x.Name, "Standard");
if (doc.TextStyles.Count() > 0) { doc.Header.CurrentTextStyleName = first(doc.TextStyles, x => x.Name, "Standard");
    try { doc.Header.DimensionTextStyleName = first(doc.TextStyles, x => x.Name, "Standard"); } catch { } }
doc.Header.CurrentLayerName = first(doc.Layers, x => x.Name, "0");
doc.Header.CurrentLineTypeName = first(doc.LineTypes, x => x.Name, "ByLayer");
foreach (var ly in doc.Layers) if (ly.Name.EndsWith("PAFTA-SINIRI") || ly.Name == "Defpoints") ly.PlotFlag = false;   // çizilmeyen pafta sınırı
doc.Header.Version = ver switch { "AC1027" => ACadVersion.AC1027, "AC1018" => ACadVersion.AC1018, "AC1024" => ACadVersion.AC1024, _ => ACadVersion.AC1032 };
using (var w = new DwgWriter(outp, doc)) { w.Write(); }
// geri okuma kontrolü
CadDocument back;
using (var rr = new DwgReader(outp)) { back = rr.Read(); }
int atr(CadDocument d) => d.Entities.OfType<ACadSharp.Entities.Insert>().Sum(i => i.Attributes.Count(a => !string.IsNullOrEmpty(a.Value)));
int atn(CadDocument d) => d.Entities.OfType<ACadSharp.Entities.Insert>().Sum(i => i.Attributes.Count);
int ins(CadDocument d) => d.Entities.OfType<ACadSharp.Entities.Insert>().Count();
Console.WriteLine($"varlık: dxf={doc.Entities.Count()} dwg={back.Entities.Count()} katman={back.Layers.Count()} blok={back.BlockRecords.Count()} insert: dxf={ins(doc)} dwg={ins(back)} öznitelik: dxf={atn(doc)}/{atr(doc)} dwg={atn(back)}/{atr(back)}");
foreach (var ly in back.Layers) if (!ly.PlotFlag) Console.WriteLine($"çizilmeyen katman: {ly.Name}");
