# Health Insurance Visualizer
Health insurance premiums make up a significant portion of many people’s expenses. Every year, these premiums are adjusted, and switching insurance providers or plans can lead to considerable savings.
However, comparing premiums across different providers together with varying deductible (franchise) levels is often complex and confusing.

This tool (developed with Shiny and Python) simplifies this by enabling you to:

- Compare premium prices from multiple insurance providers side-by-side (similar to the official website [Priminfo](https://www.priminfo.admin.ch/de/praemien))
- Visualize how different deductible levels affect your total out-of-pocket costs (including premiums, deductibles, and the additional expenses that you need to cover).

When it comes to choosing a deductible level as an adult, the rule of thumb that you often hear is as follows:

*If your healthcare costs exceed 2000 CHF, the lowest deductible level (300 CHF) will result in the lowest total costs for you.
Otherwise, the highest deductible level (2500 CHF) is the best option.*

With this visualization tool, you will see that this is (approximately) true for all insurance providers and plans. For some plans, the critical point is slightly below 2000 CHF, for others it is slightly above.

The tool is based on the '[Health insurance premiums](https://opendata.swiss/en/dataset/health-insurance-premiums)' data, which can be found on [https://opendata.swiss](https://opendata.swiss) - the platform for open Swiss government data.
