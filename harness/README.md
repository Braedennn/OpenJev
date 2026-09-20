# OpenJev

English | [中文](README.zh.md)

OpenJev is a Jev-governed agent harness: a fork of [DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness) with [TypeSafe's Jev](https://typesafe.ai) wired in as an explicit decision layer, so any model you plug in can route, verify, screen, and ask typed questions through Jev.

It keeps dsh's **everything-is-a-plugin** architecture and its [Cordis](https://github.com/cordiverse/cordis) foundation. Upstream documentation remains the reference for the plugin and profile model: [https://deepseek-harness.github.io/deepseek-harness/](https://deepseek-harness.github.io/deepseek-harness/)

OpenJev is not affiliated with or endorsed by DeepSeek. It is built on DeepSeek Harness (`dsh`), and upstream MIT notices are kept in [LICENSE](LICENSE) and [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

## Developer preview

OpenJev is a personal fork in _developer preview_. **THERE WILL BE COMPATIBILITY-BREAKING CHANGES.**

Review the [safety notice](SAFETY.md) before running the project.

## Run from source

Install `Node.js` 22.19+ and Corepack-enabled pnpm, then:

```sh
pnpm install
pnpm run build
pnpm openjev web
```

`pnpm run build` prepares the repository artifacts. `pnpm openjev web` starts the Web UI at `http://127.0.0.1:3080` using those built artifacts. `pnpm dsh web` is the upstream-compatible alias.

## Community and support

- Submit feedback or bug reports through [GitHub Discussions](https://github.com/deepseek-ai/deepseek-harness/discussions).
- Add the [`dsh-plugin`](https://github.com/topics/dsh-plugin) topic to your plugin repository for discoverability.
- Join <a href="https://discord.gg/Ycq5dCaS4">OpenJev Discord community</a>.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## Development

Start with the [development guide](docs/development.md) and [architecture documentation](docs/architecture.md).

For agents, follow [AGENTS.md](AGENTS.md).

## Citation

```bibtex
@misc{deepseek-harness2026,
  title={OpenJev: Everything is a Plugin},
  author={DeepSeek-AI},
  year={2026},
  publisher={GitHub},
  howpublished={\url{https://github.com/deepseek-ai/deepseek-harness}},
}
```

## License

[MIT](LICENSE)

Third-party dependencies and their licenses are disclosed in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
