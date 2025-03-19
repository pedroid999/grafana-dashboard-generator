import DashboardGenerator from './ui/features/DashboardGenerator';

export default function Home() {
  return (
    <main className="min-h-screen bg-gray-50">
      <div className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <h1 className="text-2xl font-bold text-gray-900">
            Grafana Dashboard Generator
          </h1>
          <p className="mt-2 text-gray-600">
            Create Grafana dashboards using AI-powered natural language prompts
          </p>
        </div>
      </div>
      
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        <DashboardGenerator />
      </div>
      
      <footer className="bg-white border-t border-gray-200 mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <p className="text-center text-gray-500 text-sm">
            &copy; {new Date().getFullYear()} Grafana Dashboard Generator - Built with Next.js and LangGraph
          </p>
        </div>
      </footer>
    </main>
  );
} 