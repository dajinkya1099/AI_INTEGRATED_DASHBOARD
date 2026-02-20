export default function CustomResponse() {

  const reactCode = `
  <!DOCTYPE html>
  <html lang="en">
  <head>
      <meta charset="UTF-8" />
      <script src="https://unpkg.com/react@18/umd/react.development.js"></script>
      <script src="https://unpkg.com/react-dom@18/umd/react-dom.development.js"></script>
      <script src="https://unpkg.com/recharts@2.8.0/umd/Recharts.js"></script>
      <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
  </head>
  <body>
      <div id="root"></div>
      <script type="text/babel">
          const App = () => {
              const data = [{ count: 10 }];
              return (
                  <div>
                      <Recharts.BarChart width={500} height={300} data={data}>
                          <Recharts.XAxis dataKey="count" />
                          <Recharts.YAxis />
                          <Recharts.Bar dataKey="count" fill="#66d9ef" />
                      </Recharts.BarChart>
                  </div>
              );
          };
          ReactDOM.createRoot(document.getElementById('root')).render(<App />);
      </script>
  </body>
  </html>
  `;

  return (
    <div style={{ padding: 40 }}>
      <h2>Hardcoded Chart Test</h2>

      <iframe
        title="chart"
        srcDoc={reactCode}
        style={{
          width: "100%",
          height: "500px",
          border: "1px solid #ccc"
        }}
        sandbox="allow-scripts allow-same-origin"
      />
    </div>
  );
}
