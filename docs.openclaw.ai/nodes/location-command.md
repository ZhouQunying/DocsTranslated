# Location Command

**总结：** 节点的 location command (`location.get`)、权限模式和 Android foreground 行为。

> **类比：iOS/Android 的 CoreLocation API。** 应用请求权限（While Using/Always）、精度（precise/coarse），OS 决定实际授权。OpenClaw 的 location.get 同理——节点在设置里声明请求模式，实际权限由 OS 控制。
>
> **架构要点：** 经 `node.invoke` 调用 `location.get`；默认关闭；设置项 `location.enabledMode`（off/whileUsing）+ `location.preciseEnabled`；返回 lat/lon、accuracy、altitude、speed、heading、source；Android foreground-only（后台返回 `LOCATION_BACKGROUND_UNAVAILABLE`）；错误码：`LOCATION_DISABLED`、`LOCATION_PERMISSION_REQUIRED`、`LOCATION_TIMEOUT`、`LOCATION_UNAVAILABLE`。
