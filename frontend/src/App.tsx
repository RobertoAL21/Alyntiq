import { AnimatePresence, MotionConfig, motion } from "motion/react";
import { Navigate, Route, Routes, useLocation } from "react-router-dom";

import { AppShell } from "./components/AppShell";
import { MarketPage } from "./pages/MarketPage";
import { ModelsPage } from "./pages/ModelsPage";
import { OverviewPage } from "./pages/OverviewPage";
import { PositionsPage } from "./pages/PositionsPage";
import { StrategiesPage } from "./pages/StrategiesPage";
import { TradesPage } from "./pages/TradesPage";

export function App() {
  const location = useLocation();

  return (
    <MotionConfig reducedMotion="user">
      <AppShell>
        <AnimatePresence mode="wait">
          <motion.div
            key={location.pathname}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            transition={{ duration: 0.24, ease: "easeOut" }}
          >
            <Routes location={location}>
              <Route path="/" element={<OverviewPage />} />
              <Route path="/positions" element={<PositionsPage />} />
              <Route path="/trades" element={<TradesPage />} />
              <Route path="/strategies" element={<StrategiesPage />} />
              <Route path="/models" element={<ModelsPage />} />
              <Route path="/market" element={<MarketPage />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </motion.div>
        </AnimatePresence>
      </AppShell>
    </MotionConfig>
  );
}
