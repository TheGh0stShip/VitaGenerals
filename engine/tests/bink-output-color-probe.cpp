// SPDX-License-Identifier: GPL-3.0-or-later
// Compile the production decoder mapping and FFmpeg conversion together.
#include "../port/src/VitaBinkVideoDecoder.cpp"
#include <assert.h>
#include <string.h>
int main() {
  const uint8_t rgb[] = {255,0,0,0,255,0,0,0,255};
  const uint8_t expected[] = {0,0,255,0,255,0,255,0,0};
  uint8_t destination[16]; memset(destination, 0xa5, sizeof(destination));
  const uint8_t *source_planes[4] = {rgb, NULL, NULL, NULL};
  int source_pitch[4] = {9,0,0,0};
  uint8_t *destination_planes[4] = {destination,NULL,NULL,NULL};
  int destination_pitch[4] = {16,0,0,0};
  SwsContext *context = sws_getContext(3,1,AV_PIX_FMT_RGB24,3,1,
      OutputFormat(VitaBinkVideoDecoder::PixelR8G8B8),SWS_POINT,NULL,NULL,NULL);
  assert(context != NULL);
  assert(sws_scale(context,source_planes,source_pitch,0,1,
                   destination_planes,destination_pitch)==1);
  assert(memcmp(destination,expected,sizeof(expected))==0);
  sws_freeContext(context);
}
