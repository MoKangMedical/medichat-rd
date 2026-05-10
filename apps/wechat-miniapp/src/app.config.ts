export default defineAppConfig({
  pages: [
    "pages/home/index",
    "pages/deeprare/index",
    "pages/community/index",
    "pages/checkin/index",
    "pages/profile/index"
  ],
  window: {
    navigationBarTitleText: "MediChat-RD",
    navigationBarBackgroundColor: "#fffaf2",
    navigationBarTextStyle: "black",
    backgroundColor: "#fdf8ef",
    backgroundTextStyle: "light"
  },
  tabBar: {
    color: "#7e6d56",
    selectedColor: "#0b9b7a",
    backgroundColor: "#fffaf2",
    list: [
      {
        pagePath: "pages/home/index",
        text: "首页"
      },
      {
        pagePath: "pages/deeprare/index",
        text: "DeepRare"
      },
      {
        pagePath: "pages/community/index",
        text: "社群"
      },
      {
        pagePath: "pages/checkin/index",
        text: "随访"
      },
      {
        pagePath: "pages/profile/index",
        text: "我的"
      }
    ]
  }
})
