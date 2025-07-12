package com.equinor.neqsimapi.dto;

/**
 * Data transfer object returned from the REST API.
 *
 * <p>The fields correspond to various key performance indicators calculated by
 * the underlying process model. All fields are public to ease JSON
 * serialisation.</p>
 */

import java.io.PrintWriter;
import java.io.StringWriter;
import javax.xml.bind.annotation.XmlRootElement;
import neqsim.processSimulation.measurementDevice.HydrateEquilibriumTemperatureAnalyser;
import neqsim.processSimulation.measurementDevice.WaterDewPointAnalyser;
import neqsim.processSimulation.processEquipment.absorber.SimpleTEGAbsorber;
import neqsim.processSimulation.processEquipment.absorber.WaterStripperColumn;
import neqsim.processSimulation.processEquipment.distillation.Condenser;
import neqsim.processSimulation.processEquipment.distillation.DistillationColumn;
import neqsim.processSimulation.processEquipment.distillation.Reboiler;
import neqsim.processSimulation.processEquipment.filter.Filter;
import neqsim.processSimulation.processEquipment.heatExchanger.HeatExchanger;
import neqsim.processSimulation.processEquipment.pump.Pump;
import neqsim.processSimulation.processEquipment.stream.Stream;
import neqsim.processSimulation.processEquipment.util.Calculator;
import neqsim.processSimulation.processEquipment.heatExchanger.Heater;
import neqsim.processSimulation.processEquipment.separator.Separator;
import neqsim.processSimulation.processEquipment.valve.ThrottlingValve;
import neqsim.processSimulation.util.monitor.*;

/**
 *
 * @author jo.lyshoel
 */
@XmlRootElement
public class CalcResponse {

        /** Whether the simulation finished successfully */
        public boolean success;
        /** Human readable error message if {@link #success} is {@code false} */
        public String errormessage;
        /** Stack trace or underlying exception string */
        public String underlying_error;

	/**
	 * The hydrate dew point of the dehydrated gas leaving the TEB absorber
	 * (Celcius)
	 */
	public Double esthydratedewtemperature;

	/**
	 * The water dew point of the dehydrated gas leaving the TEB absorber (Celcius)
	 */
	public Double estwaterdewtemperature;

	/**
	 * The flow resistance coefficient of the fine filter
	 */
	public Double fineFilterCv;

	/**
	 * The reboiler duty (kW)
	 */
	public Double reboilerDutykW;

	/**
	 * TEG in condensed water from overhead receiver 
	 */
	public Double tegInWaterFromOHReceiver;

	/**
	 * Temperature of the rich TEG after reflux condenser (Celcius)
	 */
	public Double temperatureRichTEGafterRefluxCondenser;

	/**
	 * Hydrate temperature of gas from feed gas scrubber
	 */
	public Double hydrateTemperatureFeedGas;

	/**
	 * TEG in dry gas (kg/hr)
	 */
	public Double tEGinDryGas;


	/**
	 * Hydrate temperature of gas from feed gas to TEG absorber
	 */
	public Double hydrateTemperatureFeedGasToAbsorber;


	/**
	 * Water dew point of gas from feed gas to TEG absorber
	 */
	public Double waterDewPointFeedGasToAbsorber;

	/**
	 * Fs factor for TEG absorber (Fs = vs * sqrt(density*g), unit Pa^1/2)
	 */
	public Double absorberFsFactor;

	/**
	 * Fs factor for still column (Fs = vs * sqrt(density*g), unit Pa^1/2)
	 */
	public Double stillColumnFsFactor;

	/**
	 * TEG absorber gas load factor (Ks unit m/s)
	 */
	public Double absorberGasLoadFactor;

	/**
	 * Flash Drum gas load factor (Ks unit m/s)
	 */
	public Double flashDrumGasLoadFactor;

	/**
	 * Water content in wet feed gas (ppm (mole))
	 */
	public Double waterInWetGasppm;

	/**
	 * The water in the dehydrate gas leaving the TEB absorber (ppm (mole))
	 */
	public Double waterInDryGasppm;

	/**
	 * The flow rate of wet gas to absorber (kg/hr)
	 */
	public Double wetGasRatekghr;

	/**
	 * The water content of the wet gas (kg/MSm3)
	 */
	public Double waterInWetGaskgMSm3;

	/**
	 * The water content of the dry gas (kg/MSm3)
	 */
	public Double waterInDryGaskgMSm3;

	/**
	 * The wt% TEG from reboiler (wt%)
	 */
	public Double wtLeanTEGFromReboiler;

	/**
	 * wt% TEG in dry TEG (wt%)
	 */
	public Double waterInDryTEGwt;

	/**
	 * Absorber wetting rate (m3/m2/hr)
	 */
	public Double absorberWettingRate;

	/**
	 * The wt% TEG from stripping column (wt%)
	 */
	public Double wtLeanTEGFromStripper;

	/**
	 * The wt% in rich TEG from absorber column (wt%)
	 */
	public Double wtRichTEGFromAbsorber;

	/**
	 * The temperature of the rich TEG from the absorber
	 */
	public Double richTEGtemperature;

	/**
	 * The water in the rich TEG (kg/hr)
	 */
	public Double waterInRichTEGkghr;

	/**
	 * The TEG circulation rate per kg of water removed (litre TEG/kg water)
	 */
	public Double tEGcirculationratelitreperkg;

	/**
	 * The rich TEG temperature after depressuration (Celcius)
	 */
	public Double richTEGtemperatureAfterDepres;

	/**
	 * The condenser duty of the regeneration (kW)
	 */
	public Double condenserdutykW;

	/**
	 * The TEG makeup rate (kg/hr)
	 */
	public Double TEGmakeupkghr;

	/**
	 * The HP pump duty (kW)
	 */
	public Double pumpDutykW;

	/**
	 * The flash gas rate (kg/hr)
	 */
	public Double flashGasRate;

	/**
	 * The gas rate to flare (kg/hr)
	 */
	public Double gasToFlareRatekghr;

	/**
	 * Hydrocarbons in lean TEG (mg HC/kg lean TEG)
	 */
	public Double hCinleanTEGmgperkg;

	/**
	 * Water/TEG to water treatment (kg/hr)
	 */
	public Double waterToTreatment;

	/**
	 * TEG in water to treatment (wt%)
	 */
	public Double tEGinwatertoTreatmentwtprecent;

	/**
	 * Rich TEG flow rate (kg/hr)
	 */
	public Double richTEGflow;

        /** Heat exchanger responses for the main coolers */
        public HXResponse coldLeanHX, hotLeanHX,condenserHX ;
        /** Stream data for the condenser outlet */
        public StreamResponse overheadCondenserStream;
	/**
	*
	* Flash Gas stream
	*/
	//public StreamResponse flashGasStream;

        /**
         * Create an empty response instance.
         */
        public CalcResponse() {
        }

        /**
         * Populate the response based on a finished process simulation.
         *
         * @param operation the executed process system
         */
        public CalcResponse(neqsim.processSimulation.processSystem.ProcessSystem operation) {
		waterInDryGasppm = ((SimpleTEGAbsorber) operation.getUnit("TEG absorber")).getGasOutStream().getFluid()
				.getPhase("gas").getComponent("water").getx() * 1.0e6;
		estwaterdewtemperature = ((WaterDewPointAnalyser) operation
				.getMeasurementDevice("water dew point analyser")).getMeasuredValue("C");
		esthydratedewtemperature = ((HydrateEquilibriumTemperatureAnalyser) operation
				.getMeasurementDevice("hydrate dew point analyser")).getMeasuredValue("C");
		waterDewPointFeedGasToAbsorber = ((WaterDewPointAnalyser) operation
				.getMeasurementDevice("water dew point gas to absorber")).getMeasuredValue("C");
		reboilerDutykW = ((Reboiler) ((DistillationColumn) operation.getUnit("TEG regeneration column")).getReboiler())
				.getDuty() / 1.0e3;
		waterInWetGasppm = ((Stream) operation.getUnit("water saturated feed gas")).getFluid().getPhase(0)
				.getComponent("water").getz() * 1.0e6;
		wetGasRatekghr = ((Stream) operation.getUnit("water saturated feed gas")).getFlowRate("kg/hr");
		waterInWetGaskgMSm3 = (((Stream) operation.getUnit("water saturated feed gas")).getFluid().getPhase(0)
				.getComponent("water").getz() * 1.0e6) * 0.01802 * 101325.0 / (8.314 * 288.15);
		waterInDryGaskgMSm3 = (((Stream) operation.getUnit("dry gas from absorber")).getFluid().getPhase(0)
				.getComponent("water").getz() * 1.0e6) * 0.01802 * 101325.0 / (8.314 * 288.15);
		wtLeanTEGFromReboiler = ((Stream) ((DistillationColumn) operation.getUnit("TEG regeneration column"))
				.getLiquidOutStream()).getFluid().getPhase("aqueous").getWtFrac("TEG") * 100.0;
		wtLeanTEGFromStripper = ((WaterStripperColumn) operation.getUnit("TEG stripper")).getLiquidOutStream()
				.getFluid().getPhase("aqueous").getWtFrac("TEG") * 100.0;
		wtRichTEGFromAbsorber = ((SimpleTEGAbsorber) operation.getUnit("TEG absorber")).getSolventOutStream().getFluid()
				.getPhase("aqueous").getWtFrac("TEG") * 100.0;
		richTEGtemperature = ((SimpleTEGAbsorber) operation.getUnit("TEG absorber")).getSolventOutStream().getFluid()
				.getTemperature("C");
		waterInRichTEGkghr = ((SimpleTEGAbsorber) operation.getUnit("TEG absorber")).getSolventOutStream().getFluid()
				.getPhase("aqueous").getWtFrac("water")
				* ((SimpleTEGAbsorber) operation.getUnit("TEG absorber")).getSolventOutStream().getFluid()
						.getFlowRate("kg/hr");
		tEGcirculationratelitreperkg = ((SimpleTEGAbsorber) operation.getUnit("TEG absorber")).getSolventInStream()
				.getFlowRate("kg/hr")
				* ((WaterStripperColumn) operation.getUnit("TEG stripper")).getLiquidOutStream().getFluid()
						.getPhase("aqueous").getWtFrac("TEG")
				* 100.0 / 100
				/ ((((Stream) operation.getUnit("water saturated feed gas")).getFluid().getPhase(0)
						.getComponent("water").getz() * 1.0e6) * 0.01802 * 101325.0 / (8.314 * 288.15)
						* ((Stream) operation.getUnit("dry feed gas")).getFlowRate("Sm3/day") / 1.0e6 / 24.0);
		richTEGtemperatureAfterDepres = ((ThrottlingValve) operation.getUnit("Rich TEG HP flash valve")).getOutStream()
				.getFluid().getTemperature("C");
		temperatureRichTEGafterRefluxCondenser =((Stream) ((Heater) operation.getUnit("rich TEG preheater")).getOutStream()).getTemperature("C");
		condenserdutykW = ((Condenser) ((DistillationColumn) operation.getUnit("TEG regeneration column"))
				.getCondenser()).getDuty() / 1.0e3;
		TEGmakeupkghr = ((Calculator) operation.getUnit("TEG makeup calculator")).getOutputVariable().getFluid()
				.getFlowRate("kg/hr");
		pumpDutykW = ((Pump) operation.getUnit("lean TEG HP pump")).getEnergy() / 1.0e3;
		flashGasRate = ((Stream) operation.getUnit("gas from degasing separator")).getFlowRate("kg/hr");
		gasToFlareRatekghr = ((Stream) operation.getUnit("gas to flare")).getFlowRate("kg/hr");
		hCinleanTEGmgperkg = (1.0
				- ((WaterStripperColumn) operation.getUnit("TEG stripper")).getLiquidOutStream().getFluid().getPhase(0)
						.getWtFrac("TEG")
				- ((WaterStripperColumn) operation.getUnit("TEG stripper")).getLiquidOutStream().getFluid().getPhase(0)
						.getWtFrac("water"))
				* 1e6;
		waterToTreatment = ((Stream) operation.getUnit("water to treatment")).getFlowRate("kg/hr");
		tEGinwatertoTreatmentwtprecent = ((Stream) operation.getUnit("water to treatment")).getFluid()
				.getPhase("aqueous").getWtFrac("TEG") * 100.0;
		richTEGflow = ((SimpleTEGAbsorber) operation.getUnit("TEG absorber")).getSolventOutStream()
				.getFlowRate("kg/hr");
		waterInDryTEGwt = ((Stream) operation.getUnit("lean TEG to absorber")).getFluid().getPhase("aqueous")
				.getWtFrac("water")*100;
		hydrateTemperatureFeedGas = ((HydrateEquilibriumTemperatureAnalyser) operation
				.getMeasurementDevice("hydrate temperature analyser")).getMeasuredValue("C");
		hydrateTemperatureFeedGasToAbsorber = ((HydrateEquilibriumTemperatureAnalyser) operation
				.getMeasurementDevice("hydrate temperature gas to absorber")).getMeasuredValue("C");
		absorberFsFactor =  ((SimpleTEGAbsorber) operation.getUnit("TEG absorber")).getFsFactor();
		absorberGasLoadFactor =  ((SimpleTEGAbsorber) operation.getUnit("TEG absorber")).getGasLoadFactor();
		flashDrumGasLoadFactor =  ((Separator) operation.getUnit("degasing separator")).getGasLoadFactor();
		stillColumnFsFactor =  ((DistillationColumn) operation.getUnit("TEG regeneration column")).getFsFactor();
		absorberWettingRate = ((SimpleTEGAbsorber) operation.getUnit("TEG absorber")).getWettingRate();
		tEGinDryGas = ((Stream) operation.getUnit("dry gas from absorber")).getFluid().getComponent("TEG").getFlowRate("kg/hr");
		tegInWaterFromOHReceiver =  ((Stream) operation.getUnit("water to treatment")).getFluid().getPhase("aqueous").getWtFrac("TEG") * 100.0;
		fineFilterCv = ((Filter) operation.getUnit("TEG fine filter")).getCvFactor();
		hotLeanHX =  new HXResponse((HeatExchanger) operation.getUnit("rich TEG heat exchanger 1")); 
		coldLeanHX =  new HXResponse((HeatExchanger) operation.getUnit("lean/rich TEG heat-exchanger")); 
		condenserHX =  new HXResponse((HeatExchanger) operation.getUnit("overhead condenser heat-exchanger")); 
		overheadCondenserStream = new StreamResponse((Stream)((HeatExchanger) operation.getUnit("overhead condenser heat-exchanger")).getOutStream(0));
		success = true;
	}

	public CalcResponse(Exception ex) {
		try {
			this.errormessage = ex.getMessage();
			StringWriter sw = new StringWriter();
			PrintWriter pw = new PrintWriter(sw);
			ex.printStackTrace(pw);
			this.underlying_error = sw.toString();
		} catch (Exception e) {
		}
	}
}
