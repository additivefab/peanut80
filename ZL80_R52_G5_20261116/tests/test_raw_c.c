#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "zl80_raw.h"
int main(void){
 const uint8_t expected[16]={0x78,0x56,0x34,0x12,0x08,0x07,0x06,0x05,0x04,0x03,0x02,0x01,0xaa,0x55,0x01,0x01};
 zl80_record r;uint8_t out[16];
 assert(zl80_decode(expected,16,&r)==0);
 assert(r.payload==0x12345678u && r.tick==UINT64_C(0x0102030405060708));
 assert(r.flags==0x55aau && r.type==1 && r.version==1);
 assert(zl80_encode(out,16,&r)==0 && memcmp(out,expected,16)==0);
 assert(zl80_decode(expected,15,&r)!=0);
 assert(zl80_decode(NULL,16,&r)!=0);
 r.version=2;assert(zl80_encode(out,16,&r)!=0);
 puts("PASS native C raw record ABI test");return 0;
}
