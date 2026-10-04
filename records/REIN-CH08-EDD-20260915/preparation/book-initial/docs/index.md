---
layout: home
hero:
  name: 'Rein'
  text: '从零手写一个 Agent Harness'
  tagline: '一条面向 Agent 学习者与求职者的工程实践路线：从模型调用，到可审查、可验证的工作区助手。'
  image:
    src: /mark.svg
    alt: Rein mark
  actions:
    - theme: brand
      text: 开始阅读
      link: /about.html
    - theme: alt
      text: 查看全书目录
      link: /toc.html
features:
  - title: 一个连续项目
    details: 围绕同一个 Rein 工作区助手，沿共同章节逐步完成模型调用、工具执行与结果验证。
  - title: 工程证据
    details: 每个阶段都对应运行记录、失败测试、架构图与可展示的成果。
  - title: 分阶段实现
    details: 01–03 章先用 TypeScript 建立直觉；05 章以后由 Rust core 承担权威运行时，TypeScript 负责受控扩展。
---

<div class="home-note">
  <span class="home-note__label">建设中 / 内容开放说明</span>
  <p>本书目前限时免费。持续更新过程中，部分章节将逐步转为收费；标注“永久免费”的章节将保持免费开放。<a href="/Rein/access.html">查看完整说明 →</a></p>
</div>

## 现在可以读什么

默认从[第 01 章 TypeScript 正文（修订中）](./chapters/01.md)开始理解真实调用，Rust hello 是可选准备。需要补充终端、HTTP、配置、类型、异步或错误处理知识时，再按需查阅[阅读 0 公共导读](./readings/00.md)及 [TS](./readings/00-ts.md) / [Rust](./readings/00-rust.md) 版。05–07 章沿 Rust core 与 TypeScript plugin 的混合路线推进，当前 M1 已完成离线实验核验；旧 TS 页面保留为历史对照。阅读 0 的示例与练习是可选自测，不是进入正文的条件。

<span id="先从一次完整任务开始"></span>

## 这条路线要走到哪里

Rein 最终要完成的事情很朴素：理解一个工作区任务，读取相关文件，提出一份人类可以审查的差异，等待批准，执行修改，并用验证器确认结果。全书从这个终点倒推，每一章只增加一个主要难点。

## 写给谁

如果你准备应聘 Agent 应用、AI 应用工程或开发者工具相关岗位，这本书会把“会调用模型”推进到“能解释一个可靠系统为什么这样工作”。你将拥有一份可以运行、演示、评测并在面试中展开讨论的项目。

<div class="home-links"><a href="/Rein/about.html">阅读指南 →</a><a href="/Rein/toc.html">完整目录 →</a><a href="/Rein/access.html">开放说明 →</a><a href="https://github.com/JadeSnow7/Rein">GitHub →</a></div>
