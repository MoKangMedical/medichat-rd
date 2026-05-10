const path = require("path");

const config = {
  projectName: "medichat-rd-wechat-miniapp",
  date: "2026-05-10",
  designWidth: 375,
  deviceRatio: {
    375: 2,
    750: 1,
    828: 1.81
  },
  sourceRoot: "src",
  outputRoot: "dist",
  plugins: [],
  defineConstants: {},
  copy: {
    patterns: [],
    options: {}
  },
  framework: "react",
  compiler: {
    type: "webpack5",
    prebundle: {
      enable: false
    }
  },
  cache: {
    enable: false
  },
  mini: {},
  h5: {
    publicPath: "/",
    staticDirectory: "static"
  },
  alias: {
    "@": path.resolve(__dirname, "..", "src")
  }
};

module.exports = function (merge) {
  const baseConfig = config;
  if (process.env.NODE_ENV === "development") {
    return merge({}, baseConfig, require("./dev"));
  }
  return merge({}, baseConfig, require("./prod"));
};
