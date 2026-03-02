export function processAIConfig(data, config) {
  if (!data || data.length === 0) return [];

  let result = [...data];

  const {
    groupBy,
    aggregation,
    xKey,
    yKey,
    sortBy,
    order,
    limit
  } = config;

  // ================= GROUP + AGGREGATE =================
  if (groupBy && aggregation) {
    const grouped = {};

    result.forEach((item) => {
      const key = item[groupBy];

      if (!grouped[key]) {
        grouped[key] = [];
      }

      grouped[key].push(item);
    });

    result = Object.keys(grouped).map((key) => {
      const items = grouped[key];

      let aggregatedValue = 0;

      switch (aggregation) {
        case "count":
          aggregatedValue = items.length;
          break;

        case "sum":
          aggregatedValue = items.reduce(
            (sum, i) => sum + Number(i[yKey] || 0),
            0
          );
          break;

        case "avg":
          aggregatedValue =
            items.reduce(
              (sum, i) => sum + Number(i[yKey] || 0),
              0
            ) / items.length;
          break;

        case "min":
          aggregatedValue = Math.min(
            ...items.map((i) => Number(i[yKey] || 0))
          );
          break;

        case "max":
          aggregatedValue = Math.max(
            ...items.map((i) => Number(i[yKey] || 0))
          );
          break;

        default:
          aggregatedValue = 0;
      }

      return {
        [xKey]: key,
        [yKey]: aggregatedValue
      };
    });
  }

  // ================= SORT =================
  if (sortBy) {
    result.sort((a, b) => {
      if (order === "desc") {
        return b[sortBy] > a[sortBy] ? 1 : -1;
      }
      return a[sortBy] > b[sortBy] ? 1 : -1;
    });
  }

  // ================= LIMIT =================
  if (limit) {
    result = result.slice(0, limit);
  }

  return result;
}