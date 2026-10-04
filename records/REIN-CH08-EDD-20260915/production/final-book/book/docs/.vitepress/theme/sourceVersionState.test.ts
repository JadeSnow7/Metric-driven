import assert from 'node:assert/strict'
import test from 'node:test'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { resolveAnchorHash, sourceEditions, sourcePathFor, sourceTopicForPath } from './sourceVersionState'

test('resolves the TypeScript and Rust language routes', () => {
  assert.equal(sourceTopicForPath('/readings/00-rust.html'), 'reading-00')
  assert.equal(sourceTopicForPath('/chapters/01-rust.html'), 'chapter-01')
  assert.equal(sourcePathFor('chapter-01', 'rust'), '/chapters/01-rust.html')
  assert.equal(sourcePathFor('chapter-01', 'ts'), '/chapters/01.html')
})

test('keeps only recognized common anchors and maps language-specific aliases', () => {
  const reading = sourceEditions['reading-00']
  assert.equal(resolveAnchorHash('setup', reading), '#setup')
  assert.equal(resolveAnchorHash('ownership', reading), '#types')
  assert.equal(resolveAnchorHash('modules', reading), '#source')
  assert.equal(resolveAnchorHash('exercise-03', reading), '#exercise-03')
  assert.equal(resolveAnchorHash('terminal', reading), '')
  assert.equal(resolveAnchorHash('install', reading, 'setup'), '#setup')
  assert.equal(resolveAnchorHash('detail', reading, 'terminal'), '')
  assert.equal(resolveAnchorHash(undefined, reading), '')
})

test('keeps chapter 01 common anchors available to both editions', () => {
  const chapter = sourceEditions['chapter-01']
  assert.equal(resolveAnchorHash('failures', chapter), '#failures')
  assert.equal(resolveAnchorHash('comparison', chapter), '')
  assert.equal(resolveAnchorHash('recording', chapter), '')
  assert.equal(resolveAnchorHash('legacy', chapter), '')
})

test('does not invent language pairs for core and legacy chapter routes', () => {
  assert.equal(sourceTopicForPath('/chapters/05-rust.html'), undefined)
  assert.equal(sourceTopicForPath('/chapters/06-rust.html'), undefined)
  assert.equal(sourceTopicForPath('/chapters/07-rust.html'), undefined)
  assert.equal(sourceTopicForPath('/chapters/05.html'), undefined)
  assert.equal(sourceTopicForPath('/chapters/06.html'), undefined)
  assert.equal(sourceTopicForPath('/chapters/07.html'), undefined)
})

test('sidebar uses the Rust core route and exposes the plugin adjunct', () => {
  const config = readFileSync(resolve(import.meta.dirname, '../config.mts'), 'utf8')
  assert.match(config, /05 核心 Agent Loop（Rust core）.*\/chapters\/05-rust\.html/)
  assert.match(config, /06 循环控制（Rust core）.*\/chapters\/06-rust\.html/)
  assert.match(config, /06 插件附页.*\/chapters\/06-plugin\.html/)
  assert.match(config, /07 上下文管理（Rust core）.*\/chapters\/07-rust\.html/)
})
