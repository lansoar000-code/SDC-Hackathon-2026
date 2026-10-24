// Translate service-owned messages for display without changing the API payloads.
const messages = new Map([
  ["模拟演示：固定示例规则，不使用真实销量或训练模型。", "Simulated demo: fixed example rules, with no real sales data or trained model."],
  ["包含明确标识的合成食堂数据；预测与评估只反映模拟场景，不代表真实餐厅效果。", "This plan uses labelled synthetic cafeteria data. Forecasts and evaluations describe simulated conditions, not real restaurant performance."],
  ["训练数据与本次可用历史不一致，已改用历史基线；可重新训练。", "The saved model does not match the available history. A historical baseline was used; retrain to update the model."],
  ["当前使用历史基线；天气、考试周和活动不会被人为加成。", "Historical baseline: no manual adjustments for weather, exam week or local events."],
  ["基线菜品仅依据历史销量；天气、考试周和活动暂不影响这些菜品。", "Baseline dishes use sales history only. Weather, exam week and events do not affect these forecasts."],
  ["模型尚未在独立真实测试集验证；历史条件缺失会限制对应因素的学习。", "The model has not been validated on an independent real-world test set. Missing historical conditions limit what it can learn."],
  ["目标日期之前没有历史销量，请先导入数据，或选择模拟演示", "No sales history exists before the forecast date. Import sales or select Simulated demo."],
  ["模型文件损坏或不兼容，请重新训练，或明确选择基线模式", "The saved model is damaged or incompatible. Retrain it or select Historical baseline."],
  ["按日期滚动单步验证，较早验证日的实际销量可供之后日期使用；验证集用于模型选择，不是独立测试集。", "Rolling one-step validation uses earlier actual sales for later dates. The validation set is used for model selection and is not an independent test set."],
  ["主指标取同日期同菜品最后一条事前预测；表格取最新预测，补做历史记录标 retrospective。WAPE 为误差率，分母为零时为空。", "Metrics use the latest advance forecast per date and dish. The table uses the latest forecast and labels retrospective records. WAPE is an error rate; it is unavailable when actual sales total zero."],
  ["请检查输入字段", "Check the input fields."],
  ["服务处理失败，请查看运行窗口中的错误记录", "The service could not complete this request. Check the server log."],
  ["找不到这条预测记录", "This forecast could not be found."],
  ["记录冲突，整批未写入，请刷新后检查重复日期和菜品", "Duplicate records were found. No rows were saved. Refresh and check the dates and dishes."],
  ["训练至少需要 21 个有销量记录的日期；数据不足时仍可使用基线预测", "Training requires at least 21 saved dates. You can still use the historical baseline."],
  ["验证起点必须是已有日期，且晚于首个历史日期", "The validation start must be a saved date after the first date in the history."],
  ["Excel 解压后超过 50 MB，请缩小文件", "The expanded Excel file exceeds 50 MB. Use a smaller file."],
  ["只支持 .csv 和 .xlsx 文件", "Only CSV and XLSX files are supported."],
  ["无法读取表格；CSV 请使用 UTF-8，Excel 请使用有效的 XLSX 文件", "The file could not be read. Use UTF-8 CSV or a valid XLSX workbook."],
  ["表格没有可导入的数据", "The file contains no rows to import."],
  ["尚未训练，自动模式使用历史基线", "No trained model is available. Automatic mode uses the historical baseline."]
]);
export function dishLabel(name) {
  return ({ "海南鸡饭": "Hainanese chicken rice", "招牌炒饭": "Signature fried rice", "清汤面": "Clear broth noodles", "炒饭": "Fried rice", "鸡饭": "Chicken rice", "面条": "Noodles" })[name] || name;
}
export function englishMessage(value) {
  const text = String(value ?? "");
  if (messages.has(text)) return messages.get(text);
  let match;
  if ((match = text.match(/^成功保存 (\d+) 条销量记录$/))) return "Saved " + match[1] + " sales records.";
  if ((match = text.match(/^(.*) 只有 (\d+) 条历史记录，结果仅供初步参考。$/))) return dishLabel(match[1]) + " has only " + match[2] + " historical records. Treat this forecast as preliminary.";
  if ((match = text.match(/^(.*) 最新记录为 (.*)；存在日期缺口或预测跨度超过一天。$/))) return "The latest record for " + dishLabel(match[1]) + " is " + match[2] + ". History has gaps or the forecast is more than one day ahead.";
  if ((match = text.match(/^文件不能超过 ([\d.]+) MB$/))) return "The file must not exceed " + match[1] + " MB.";
  if ((match = text.match(/^最多导入 (\d+) 行，请分批处理$/))) return "Import up to " + match[1] + " rows at a time.";
  if ((match = text.match(/^重复记录：(.*)；整批未写入$/))) return "Duplicate record: " + match[1] + ". No rows were saved.";
  if ((match = text.match(/^菜品 (.*) 已对应名称 (.*)，请统一名称$/))) return "Dish " + match[1] + " is already named " + dishLabel(match[2]) + ". Use a consistent name.";
  const fragments = {
    "表头不符合模板": "The file headers do not match the template",
    "数据校验失败，整批未写入": "Data validation failed; no rows were saved",
    "列数与表头不一致": "The number of columns does not match the headers",
    "日期和菜品重复": "Duplicate date and dish combination",
    "同一菜品编号对应多个名称": "A dish ID has more than one dish name",
    "实际销量不能填写未来日期": "Actual sales cannot have a future date",
    "销量不能超过备餐量": "Sales cannot exceed the prepared quantity",
    "销量加浪费量不能超过备餐量": "Sales plus waste cannot exceed the prepared quantity",
    "必须为非负整数": "must be a non-negative integer",
    "必须为整数": "must be an integer",
    "必须为 true 或 false": "must be true or false",
    "必须是 0–1000000 的整数": "must be an integer between 0 and 1,000,000",
    "必须是整数": "must be an integer",
    "仅接受 true/false、1/0、yes/no": "accepts only true/false, 1/0 or yes/no"
  };
  let translated = text;
  for (const [source, target] of Object.entries(fragments)) translated = translated.split(source).join(target);
  return translated;
}
