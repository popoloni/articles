// Synthetic determinism and freshness tests. No model or performance claims.
import test from 'node:test';
import assert from 'node:assert/strict';
import {Game, acceptDecision, activeAction, percentile} from '../core.js';
const result = {action:'up', epoch:2,seq:3,observed_at_ms:1000};
test('new, fresh decision is usable',()=>assert.equal(acceptDecision(result,2,2,1100,500),true));
test('TTL starts at observation, not receipt',()=>assert.equal(activeAction(result,2,1501,500),'stay'));
test('late result is rejected',()=>assert.equal(acceptDecision(result,2,2,1501,500),false));
test('wrong round cannot move paddle',()=>assert.equal(activeAction(result,3,1100,500),'stay'));
test('duplicate sequence rejected',()=>assert.equal(acceptDecision(result,2,3,1100,500),false));
test('future timestamp rejected',()=>assert.equal(acceptDecision(result,2,2,900,500),false));
test('unknown action rejected',()=>assert.equal(acceptDecision({...result,action:'fire'},2,2,1100,500),false));
test('percentiles use nearest rank',()=>{assert.equal(percentile([1,2,3,100],.95),100);assert.equal(percentile([],.5),null);});
test('simulation deterministic for equal seeds and actions',()=>{
 const a=new Game(42),b=new Game(42);
 for(let i=0;i<2400;i++){const act=i%300<150?'up':'down'; a.step(1/120,act);b.step(1/120,act);}
 assert.deepEqual(a.snapshot(),b.snapshot());assert.equal(a.misses,b.misses);
});
test('paddle is clamped and reset invalidates old epochs',()=>{
 const g=new Game(42), epoch=g.epoch; for(let i=0;i<240;i++)g.step(1/120,'up');
 assert.equal(g.paddleY,g.paddleHeight/2);g.reset(42);assert.ok(g.epoch>epoch);
});
test('physics advances without a model result',()=>{
 const g=new Game(42); const x=g.ballX;for(let i=0;i<120;i++)g.step(1/120,activeAction(null,g.epoch,1000,500));
 assert.ok(g.ballX<x);assert.ok(Math.abs(g.simTime-1)<1e-10);
});
test('large physics timestep is rejected',()=>assert.throws(()=>new Game().step(1,'up')));
