/* Basit giriş dosyasından LibreDWG ile R2000 DWG üretir.
   Satır formatı (TAB ayrımlı):
   Y name color ltype            -> katman
   K name dashlen gaplen         -> kesikli çizgi tipi
   L lay x1 y1 x2 y2
   C lay cx cy r
   P lay closed width n x y ...
   S lay x1 y1 x2 y2 x3 y3
   T lay h rot ha va x y ax ay text
*/
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <dwg.h>
#include <dwg_api.h>

#define MAXL 128
static char lname[MAXL][64];
static Dwg_Object_LAYER *lobj[MAXL];
static unsigned long lhnd[MAXL];
static int nl = 0;
static char tname[16][64];
static Dwg_Object_LTYPE *tobj[16];
static int nt = 0;
static int gerr = 0;

static Dwg_Object_LAYER *find_layer (const char *n)
{
  for (int i = 0; i < nl; i++)
    if (!strcmp (lname[i], n)) return lobj[i];
  return NULL;
}
static Dwg_Object_LTYPE *find_ltype (const char *n)
{
  for (int i = 0; i < nt; i++)
    if (!strcmp (tname[i], n)) return tobj[i];
  return NULL;
}

static void set_layer (Dwg_Data *dwg, void *ent, const char *n)
{
  int k = -1;
  for (int i = 0; i < nl; i++)
    if (!strcmp (lname[i], n)) { k = i; break; }
  if (k < 0) return;
  Dwg_Object *o = dwg_obj_generic_to_object (ent, &gerr);
  if (!o) return;
  o->tio.entity->layer = dwg_add_handleref (dwg, 5, lhnd[k], NULL);
}

int main (int argc, char **argv)
{
  if (argc < 3) { fprintf (stderr, "usage: mkdwg in.txt out.dwg\n"); return 1; }
  FILE *f = fopen (argv[1], "r");
  if (!f) return 1;
  Dwg_Data *dwg = dwg_new_Document (R_2000, 0, 0);
  if (!dwg) return 2;
  dwg->header_vars.INSUNITS = 4;
  dwg->header_vars.LTSCALE = 50.0;
  Dwg_Object_BLOCK_HEADER *ms = dwg_model_space_object (dwg)->tio.object->tio.BLOCK_HEADER;
  Dwg_Object_STYLE *st = dwg_add_STYLE (dwg, "ROTAS");
  if (st) { st->font_file = dwg_add_u8_input (dwg, "arial.ttf"); }
  Dwg_Object *sto0 = st ? dwg_obj_generic_to_object (st, &gerr) : NULL;
  unsigned long sth = sto0 ? sto0->handle.value : 0;

  static char line[65536];
  long cnt = 0;
  while (fgets (line, sizeof line, f))
    {
      line[strcspn (line, "\n")] = 0;
      char *tok[2048]; int n = 0;
      char *p = line;
      while (n < 2048)
        {
          tok[n++] = p;
          char *t = strchr (p, '\t');
          if (!t) break;
          *t = 0; p = t + 1;
        }
      if (n < 2) continue;
      char k = tok[0][0];
      if (k == 'H')
        {
          dwg->header_vars.INSUNITS = (short)atoi (tok[1]);
          dwg->header_vars.LTSCALE = atof (tok[2]);
          continue;
        }
      if (k == 'K')
        {
          Dwg_Object_LTYPE *lt = dwg_add_LTYPE (dwg, tok[1]);
          if (lt)
            {
              double d = atof (tok[2]), g = atof (tok[3]);
              lt->description = dwg_add_u8_input (dwg, tok[1]);
              lt->alignment = 'A';
              lt->numdashes = 2;
              lt->pattern_len = d + g;
              lt->dashes = calloc (2, sizeof (Dwg_LTYPE_dash));
              lt->dashes[0].length = d;
              lt->dashes[1].length = -g;
              lt->dashes[0].scale = lt->dashes[1].scale = 1.0;
              strncpy (tname[nt], tok[1], 63); tobj[nt++] = lt;
            }
        }
      else if (k == 'Y')
        {
          Dwg_Object_LAYER *l = dwg_add_LAYER (dwg, tok[1]);
          if (l)
            {
              l->color.index = (short)atoi (tok[2]);
              Dwg_Object_LTYPE *lt = find_ltype (tok[3]);
              if (lt)
                {
                  Dwg_Object *lto = dwg_obj_generic_to_object (lt, &gerr);
                  l->ltype = dwg_add_handleref (dwg, 5, lto->handle.value, NULL);
                }
              else
                {
                  BITCODE_H h = dwg_find_tablehandle (dwg, "CONTINUOUS", "LTYPE");
                  if (h) l->ltype = dwg_add_handleref (dwg, 5, h->absolute_ref, NULL);
                }
              if (n > 4) { int lw = atoi (tok[4]); if (lw > 0) { l->linewt = (BITCODE_RC) dxf_revcvt_lweight (lw); l->flag0 = (l->flag0 & ~0x3E0) | ((l->linewt & 0x1f) << 5); } }
              { Dwg_Object *lo2 = dwg_obj_generic_to_object (l, &gerr); lhnd[nl] = lo2 ? lo2->handle.value : 0; }
              strncpy (lname[nl], tok[1], 63); lobj[nl++] = l;
            }
        }
      else if (k == 'L')
        {
          dwg_point_3d a = { atof (tok[2]), atof (tok[3]), 0 }, b = { atof (tok[4]), atof (tok[5]), 0 };
          Dwg_Entity_LINE *e = dwg_add_LINE (ms, &a, &b);
          if (e) set_layer (dwg, e, tok[1]);
        }
      else if (k == 'C')
        {
          dwg_point_3d c = { atof (tok[2]), atof (tok[3]), 0 };
          Dwg_Entity_CIRCLE *e = dwg_add_CIRCLE (ms, &c, atof (tok[4]));
          if (e) set_layer (dwg, e, tok[1]);
        }
      else if (k == 'S')
        {
          dwg_point_3d a = { atof (tok[2]), atof (tok[3]), 0 };
          dwg_point_2d b = { atof (tok[4]), atof (tok[5]) }, c = { atof (tok[6]), atof (tok[7]) };
          Dwg_Entity_SOLID *e = dwg_add_SOLID (ms, &a, &b, &c, &c);
          if (e) set_layer (dwg, e, tok[1]);
        }
      else if (k == 'P')
        {
          int closed = atoi (tok[2]);
          double w = atof (tok[3]);
          int np = atoi (tok[4]);
          dwg_point_2d *pts = calloc (np, sizeof (dwg_point_2d));
          for (int i = 0; i < np; i++)
            { pts[i].x = atof (tok[5 + 2 * i]); pts[i].y = atof (tok[6 + 2 * i]); }
          Dwg_Entity_LWPOLYLINE *e = dwg_add_LWPOLYLINE (ms, np, pts);
          free (pts);
          if (e)
            {
              if (closed) e->flag |= 512;
              if (w > 0) { e->const_width = w; e->flag |= 4; }
              set_layer (dwg, e, tok[1]);
            }
        }
      else if (k == 'T')
        {
          dwg_point_3d ins = { atof (tok[6]), atof (tok[7]), 0 };
          Dwg_Entity_TEXT *e = dwg_add_TEXT (ms, tok[10], &ins, atof (tok[2]));
          if (e)
            {
              e->rotation = atof (tok[3]) * M_PI / 180.0;
              e->horiz_alignment = (short)atoi (tok[4]);
              e->vert_alignment = (short)atoi (tok[5]);
              e->alignment_pt.x = atof (tok[8]);
              e->alignment_pt.y = atof (tok[9]);
              e->width_factor = (n > 11) ? atof (tok[11]) : 1.0;
              if (sth) e->style = dwg_add_handleref (dwg, 5, sth, NULL);
              set_layer (dwg, e, tok[1]);
            }
        }
      cnt++;
    }
  fclose (f);
  int r = dwg_write_file (argv[2], dwg);
  fprintf (stderr, "entities/records: %ld, write: %d\n", cnt, r);
  return r >= DWG_ERR_CRITICAL ? 3 : 0;
}
