import DashboardGenerator from './ui/features/DashboardGenerator';

export default function Home() {
  return (
    <main className="min-h-screen">
      <header className="bg-white border-b border-gray-200 shadow-sm py-6">
        <div className="container-content">
          <h1 className="text-2xl font-bold">
            Grafana Dashboard Generator
          </h1>
          <p className="mt-2 text-gray-600">
            Create Grafana dashboards using AI-powered natural language prompts
          </p>
        </div>
      </header>
      
      <div className="container-content py-10">
        <DashboardGenerator />
      </div>
      
      <footer className="bg-white border-t border-gray-200 mt-16 py-6">
        <div className="container-content">
          <p className="text-center text-gray-500 text-sm">
            &copy; {new Date().getFullYear()} Grafana Dashboard Generator - Built with Next.js and LangGraph
          </p>
        </div>
      </footer>
    </main>
  );
} 