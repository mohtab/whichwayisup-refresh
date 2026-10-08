/* Visible-region bilinear sampler, derived from pygame 2.6.1 src_c/rotozoom.c.
 * Original rotozoom code: Andreas Schiffler; pygame modifications.
 * LGPL-2.1-or-later; see licenses/rotozoom-LGPL.txt and upstream source.
 * Only the iteration bounds change: coordinates retain the full output center.
 */
#include <stdint.h>
typedef struct { uint8_t r,g,b,a; } tColorRGBA;
void sample_region(const void *pixels, int width, int height, int pitch,
                  void *output, int outw, int outh, int outpitch,
                  int fullw, int fullh, int left, int top, int isin, int icos) {
 int cx=fullw/2,cy=fullh/2,sw=width-1,sh=height-1;
 int xd=(width-fullw)*32768,yd=(height-fullh)*32768;
 int ax=cx*65536-icos*cx,ay=cy*65536-isin*cx;
 for(int y=0;y<outh;y++) {
  tColorRGBA *pc=(tColorRGBA *)((uint8_t *)output+y*outpitch),*sp;
  int dy=cy-(y+top),sdx=ax+isin*dy+xd+icos*left;
  int sdy=ay-icos*dy+yd+isin*left;
  for(int x=0;x<outw;x++,pc++,sdx+=icos,sdy+=isin) {
   int dx=sdx>>16;dy=sdy>>16;
   int t1,t2,ex,ey; tColorRGBA c00,c01,c10,c11;
   if(dx>=-1 && dy>=-1 && dx<width && dy<height) {
                    if ((dx >= 0) && (dy >= 0) && (dx < sw) && (dy < sh)) {
                        sp = (tColorRGBA *)((uint8_t *)pixels +
                                            pitch * dy);
                        sp += dx;
                        c00 = *sp;
                        sp += 1;
                        c01 = *sp;
                        sp = (tColorRGBA *)((uint8_t *)sp + pitch);
                        sp -= 1;
                        c10 = *sp;
                        sp += 1;
                        c11 = *sp;
                    }
                    else if ((dx == sw) && (dy == sh)) {
                        sp = (tColorRGBA *)((uint8_t *)pixels +
                                            pitch * dy);
                        sp += dx;
                        c00 = *sp;
                        c01 = *sp;
                        c10 = *sp;
                        c11 = *sp;
                    }
                    else if ((dx == -1) && (dy == -1)) {
                        sp = (tColorRGBA *)(pixels);
                        c00 = *sp;
                        c01 = *sp;
                        c10 = *sp;
                        c11 = *sp;
                    }
                    else if ((dx == -1) && (dy == sh)) {
                        sp = (tColorRGBA *)((uint8_t *)pixels +
                                            pitch * dy);
                        c00 = *sp;
                        c01 = *sp;
                        c10 = *sp;
                        c11 = *sp;
                    }
                    else if ((dx == sw) && (dy == -1)) {
                        sp = (tColorRGBA *)(pixels);
                        sp += dx;
                        c00 = *sp;
                        c01 = *sp;
                        c10 = *sp;
                        c11 = *sp;
                    }
                    else if (dx == -1) {
                        sp = (tColorRGBA *)((uint8_t *)pixels +
                                            pitch * dy);
                        c00 = *sp;
                        c01 = *sp;
                        c10 = *sp;
                        sp = (tColorRGBA *)((uint8_t *)sp + pitch);
                        c11 = *sp;
                    }
                    else if (dy == -1) {
                        sp = (tColorRGBA *)(pixels);
                        sp += dx;
                        c00 = *sp;
                        c01 = *sp;
                        c10 = *sp;
                        sp += 1;
                        c11 = *sp;
                    }
                    else if (dx == sw) {
                        sp = (tColorRGBA *)((uint8_t *)pixels +
                                            pitch * dy);
                        sp += dx;
                        c00 = *sp;
                        c01 = *sp;
                        sp = (tColorRGBA *)((uint8_t *)sp + pitch);
                        c10 = *sp;
                        c11 = *sp;
                    }
                    else if (dy == sh) {
                        sp = (tColorRGBA *)((uint8_t *)pixels +
                                            pitch * dy);
                        sp += dx;
                        c00 = *sp;
                        sp += 1;
                        c01 = *sp;
                        c10 = *sp;
                        c11 = *sp;
                    }
                    else {
                        // NOTE: a catchall to appease gcc4 warnings...
                        // Probably should not get here.  we'll see.
                        //  old behaviour would be to use the previous pixel,
                        //  from the previous loop.
                        sp = (tColorRGBA *)(pixels);
                        c00 = *sp;
                        c01 = *sp;
                        c10 = *sp;
                        c11 = *sp;
                    }
                    /*
                     * Interpolate colors
                     */
                    ex = (sdx & 0xffff);
                    ey = (sdy & 0xffff);
                    typedef int32_t lanes __attribute__((vector_size(16)));
                    lanes a={c00.r,c00.g,c00.b,c00.a},b={c01.r,c01.g,c01.b,c01.a};
                    lanes c={c10.r,c10.g,c10.b,c10.a},d={c11.r,c11.g,c11.b,c11.a};
                    lanes u=(((b-a)*ex)>>16)+a,v=(((d-c)*ex)>>16)+c;
                    lanes out=(((v-u)*ey)>>16)+u;
                    pc->r=out[0];pc->g=out[1];pc->b=out[2];pc->a=out[3];
                }

  }
 }
}
