package com.equinor.neqsimapi.dto;

/**
 * Input parameters for a TEG dehydration/regeneration simulation.
 *
 * <p>The fields are public to simplify JSON serialisation when called from the
 * REST API. Default values match the examples used in the notebooks.</p>
 */
public class TEGdehydrationRequest {

	public double coolingMedium1FlowRate = 3448.0;
	public double coolingMedium1FeedTemperature = 18.0;
	public double coolingMedium1FeedPressure = 7.5;
	public double UAoverheadCondenser = 513.0;
	/**
	 * The flow rate of gas from the scrubber controlling the dew point (MSm3/hr)
	 */
	public double feedGasFlowRate = 10.5;

	/**
	 * The temperature of the gas from the scrubber controlling the dew point
	 * (Celisuis)
	 */
	public double feedGasTemperature = 23.0;

	/**
	 * The pressure of the gas from the scrubber controlling the dew point (bara)
	 */
	public double feedGasPressure = 65.0;

	/**
	 * The temperature of the gas entering the TEG absorption column (Celisuis)
	 */
	public double absorberFeedGasTemperature = 35.0;

	/**
	 * The pressure of the gas entering the TEG absorption column (bara)
	 */
	public double absorberFeedGasPressure = 155.0;

	/**
	 * The flow rate of lean TEG entering the absorption column (kg/hr)
	 */
	public double leanTEGFlowRate = 6862.5;

	/**
	 * The temperature of the lean TEG entering the absorption column (Celcius)
	 */
	public double leanTEGTemperature = 43.0;

	/**
	 * The pressure in the flash drum (bara)
	 */
	public double flashDrumPressure = 4.8;

	/**
	 * Number of equilibrium stages in TEG absorpber
	 */
	public int numberOfStagesTEGabsorber = 4;

	/**
	 * Stage efficiency in TEG absorpber
	 */
	public double stageEfficiencyTEGabsorber = 0.5;

	/**
	 * Number of equilibrium stages in TEG absorpber
	 */
	public int numberOfStagesStripper = 1;

	/**
	 * Stage efficiency in TEG absorpber
	 */
	public double stageEfficiencyStripper = 0.35;

	/**
	 * UA value of rich TEG heat exchanger
	 */
	public double UAvalueLeanRichTEGHeatExchanger = 8200.0;

	/**
	 * Pressure in reboiler (bara)
	 */
	public double reboilerPressure = 1.2;

	/**
	 * Hot TEG punmp out pressure bara
	 */
	public double hotTEGpumpPressure = 3.0;

	/**
	 * Temperature in condenser(Celcius)
	 */
	public double condenserTemperature = 85.0;

	/**
	 * Pressure in condenser (bara)
	 */
	public double condenserPressure = 1.0;

	/**
	 * Temperature in reboiler (Celcius)
	 */
	public double reboilerTemperature = 204.0;

	/**
	 * Stripping gas flow rate (Sm3/hr)
	 */
	public double strippingGasRate = 250.0;

	/**
	 * Stripping gas feed temperature (Celcius)
	 */
	public double strippingGasFeedTemperature = 80.0;

	/**
	 * temperature of after regeneration gas cooler (Celcius)
	 */
	public double regenerationGasCoolerTemperature = 16.0;

	/**
	 * isentropic efficiency of lean TEG pump (0.0-1.0)
	 */
	public double TEGpumpIsentropicEfficiency = 0.75;
	
	/**
	 * pressure drop over fine filter (bar
	 */
	public double finefilterdeltaP = 0.01;
	
	/**
	 * pressure drop over carbon filter (bar
	 */
	public double carbonfilterdeltaP = 0.01;
	
	/**
	 * UA value of rich TEG heat exchanger
	 */
	public double UAvalueLeanRichTEGHeatExchanger2 = 2900.0;

	/**
	 * Temperature of TEG in buffer tank
	 */
	public double bufferTankTemperatureTEG = 190.0;

		/**
	 * Hot TEG punmp adibatic effficiency
	 */
	public double hotTEGpumpIsentropicEfficiency = 0.75;

        /** Mole fraction of nitrogen in the feed gas (%) */
        public Double liftGas_N2=0.342;
        /** Mole fraction of CO2 in the feed gas (%) */
        public Double liftGas_CO2=2.49;
        /** Mole fraction of methane in the feed gas (%) */
        public Double liftGas_Methane=90.00;
        /** Mole fraction of ethane in the feed gas (%) */
        public Double liftGas_Ethane=3.9;
        /** Mole fraction of propane in the feed gas (%) */
        public Double liftGas_Propane= 1.7;
        /** Mole fraction of i-butane in the feed gas (%) */
        public Double liftGas_iButane=0.00;
        /** Mole fraction of n-butane in the feed gas (%) */
        public Double liftGas_nButane=0.00;
        /** Mole fraction of i-pentane in the feed gas (%) */
        public Double liftGas_iPentane=0.0;
        /** Mole fraction of n-pentane in the feed gas (%) */
        public Double liftGas_nPentane=0.0;

	public TEGdehydrationRequest() {

	}

    public static void main(String[] args) {

        }
        /**
         * Perform a simple sanity check of the supplied parameters.
         *
         * @return {@code true} if all required parameters are positive
         */
        public boolean checkValidInput() {
                return (feedGasFlowRate>0.001 && strippingGasRate>0 && feedGasPressure>0 && flashDrumPressure>0 && condenserPressure>0 && hotTEGpumpPressure>0 && absorberFeedGasPressure>0 && reboilerPressure>0);
        }
}
