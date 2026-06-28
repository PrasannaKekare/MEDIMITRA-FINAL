const Spinner = () => (
  <div className="flex justify-center items-center h-screen bg-veryDarkPurple/50 fixed inset-0 z-[100] backdrop-blur-sm">
    <div className="relative flex items-center justify-center">
      <div className="absolute h-24 w-24 rounded-full border-4 border-custom-purple3/20"></div>
      <div className="h-24 w-24 rounded-full border-4 border-t-custom-purple2 border-r-custom-purple3 border-b-transparent border-l-transparent animate-spin"></div>
      <div className="absolute h-16 w-16 rounded-full bg-custom-purple/20 animate-pulse blur-md"></div>
    </div>
  </div>
);
export default Spinner;