#ifndef ZL80_RAW_H
#define ZL80_RAW_H
#include <stdint.h>
#include <stddef.h>
#define ZL80_RECORD_BYTES 16u
/* This structure is a decoded in-memory object. NEVER write sizeof(struct) to DMA/file. */
typedef struct { uint32_t payload; uint64_t tick; uint16_t flags; uint8_t version,type; } zl80_record;
static inline uint32_t zl80_u32le(const uint8_t *p) {
 return (uint32_t)p[0] | ((uint32_t)p[1]<<8) | ((uint32_t)p[2]<<16) | ((uint32_t)p[3]<<24);
}
static inline void zl80_put32le(uint8_t *p,uint32_t x) {
 p[0]=(uint8_t)x;p[1]=(uint8_t)(x>>8);p[2]=(uint8_t)(x>>16);p[3]=(uint8_t)(x>>24);
}
static inline int zl80_decode(const uint8_t *p,size_t n,zl80_record *r) {
 if(!p || !r || n!=ZL80_RECORD_BYTES || p[14]!=1) return -1;
 r->payload=zl80_u32le(p);r->tick=(uint64_t)zl80_u32le(p+4)|((uint64_t)zl80_u32le(p+8)<<32);
 r->flags=(uint16_t)((uint16_t)p[12]|((uint16_t)p[13]<<8));r->version=p[14];r->type=p[15];return 0;
}
static inline int zl80_encode(uint8_t *p,size_t n,const zl80_record *r) {
 if(!p || !r || n!=ZL80_RECORD_BYTES || r->version!=1)return -1;
 zl80_put32le(p,r->payload);zl80_put32le(p+4,(uint32_t)r->tick);zl80_put32le(p+8,(uint32_t)(r->tick>>32));
 p[12]=(uint8_t)r->flags;p[13]=(uint8_t)(r->flags>>8);p[14]=r->version;p[15]=r->type;return 0;
}
#endif
